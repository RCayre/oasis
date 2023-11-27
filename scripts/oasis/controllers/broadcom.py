from oasis.controllers.controller import Controller
from oasis.controllers.analysis import patterns,exceptions,thumb
from oasis.controllers.generators import patch_generator,linker_generator,wrapper_generator,conf_generator
from oasis.interface.internalblue import InternalblueInterface
import struct

class BroadcomController(Controller):
    def __init__(self,filename):
        self.firmwarePath = filename
        with open(filename,"rb") as f:
            firmware = f.read()
        Controller.__init__(self,firmware)

    def extractFirmwareStructure(self):
        ramBaseAddress = struct.unpack("I",self.firmware[:4])[0]
        self.firmwareStructure["rom"] = (0,ramBaseAddress-1)
        if len(self.firmware) >= ramBaseAddress:
            self.firmwareStructure["ram"] = (ramBaseAddress,len(self.firmware))
        print(self.firmwareStructure)

    def extractFirmwareInformations(self):
        pattern = patterns.generatePattern([
            {"value":"0b000600"},
            {"joker":4},
            {"value":"00000900"}
        ])

        if len([address for address in patterns.findPattern(self.firmware,pattern)]) > 0:
            self.firmwareInformations["hci_implementation"] = "new"
        else:
            self.firmwareInformations["hci_implementation"] = "old"

        self.firmwareInformations["architecture"] = "armv7-m"
        self.firmwareInformations["file_type"] = "bin"
        print(self.firmwareInformations)

    def extractUtilsMemcpy8(self):
        utilsMemcpy8Address = None

        pattern = patterns.generatePattern([
            {"instruction":"push {r4,r5,r6,r7,r8,r9}"},
            {"instruction":"cmp r2,#32"}
        ])

        for address in patterns.findPattern(self.firmware, pattern):
           if self.firmware[address+6:address+8] == b"\x06\xDB":
                utilsMemcpy8Address = address

        if utilsMemcpy8Address is not None:
            return utilsMemcpy8Address
        else:
            raise exceptions.AddressNotFound

    def extractRtMemcpy(self):
        rtMemcpyAddress = None
        pattern1 = patterns.generatePattern([
             {"instruction":"cmp r2,#0x3"},
            {"joker":4},
            {"instruction":"ands r12,r0,#0x3"},
            {"joker":4},
            {"instruction":"ldrb.w r3,[r1],#1"}
        ])
        pattern2 = patterns.generatePattern([
            {"instruction":"push {r4,r6,r7,r8,r9,r10,lr}"},
            {"instruction":"cmp r2,#4"},
        ])
        for address in patterns.findPattern(self.firmware, patterns.generateAlternatives(pattern1,pattern2)):
            rtMemcpyAddress = address

        if rtMemcpyAddress is None:
            raise exceptions.AddressNotFound
        else:
            return rtMemcpyAddress

    def extractTimestampFunctions(self):
        btclkGetNatClkClkPclkAddress = None
        convertTimestampInUsAddress = None

        pattern1 = patterns.generatePattern([
            {"instruction":"<X>","X":["ldr r2,[r1,#4]", "ldr r3,[r3,#0]"]},
            {"instruction":"str <X>,[r0,#0]","X":["r2","r3"]},
        ])
        for i in patterns.findPattern(self.firmware,pattern1):
            if self.firmware[i+4:i+6] == b"\x03\x4b" or  self.firmware[i+4:i+6] == b"\x09\x68":
               btclkGetNatClkClkPclkAddress = i-2
               break
            else:
                raise exceptions.AddressNotFound
        pattern2 = patterns.generatePattern([
            {"instruction":"<X>","X":["ldr r0,[r0,#4]","ldr r0,[r0,#0]","lsrs r0,r0,#1"]},
            {"instruction":"movw <X>,#0x271","X":["r2","r3"]}
        ])

        for address in patterns.findPattern(self.firmware,pattern2):
            instructions = list(thumb.exploreInstructions(self.instructions[address-32:address]))[::-1]
            for instrIndex in range(len(instructions)-1):
                if "bx" in instructions[instrIndex+1] and "lr" in instructions[instrIndex+1]:
                    convertTimestampInUsAddress = thumb.extractInstructionAddress(instructions[instrIndex])
                    break
        if convertTimestampInUsAddress is None or btclkGetNatClkClkPclkAddress is None:
            raise exceptions.AddressNotFound
        else:
            return (btclkGetNatClkClkPclkAddress,convertTimestampInUsAddress)

    def extractBcsulpSetupWhitening(self):
        bcsulpWhiteningAddress = None
        pattern1 = patterns.generatePattern([
            {"instruction":"orr r2,r2,#0x300000"}
        ])
        for address in patterns.findPattern(self.firmware,pattern1):
            instructions = list(thumb.exploreInstructions(self.instructions[address-32:address]))
            for instrIndex in range(len(instructions)-1):
                if "ldr" in instructions[instrIndex] and "ldr" in instructions[instrIndex+1]:
                    bcsulpWhiteningAddress = thumb.extractInstructionAddress(instructions[instrIndex])
                    break
        if bcsulpWhiteningAddress is not None:
            return bcsulpWhiteningAddress
        else:
            raise exceptions.AddressNotFound


    def extractLculpCreateAccessAddress(self):
        lculpCreateAccessAddress = None
        pattern1 = patterns.generatePattern([
            {"instruction":"push {<X>,lr}","X":["r3","r4"]},
            {"joker":4},
            {"instruction":"ubfx <X>,r0,#0x0,#0xf;ubfx r1,<X>,#0x4,#0x1","X":["r3","r0"]},
        ])
        pattern2 = patterns.generatePattern([
            {"instruction":"push {<X>,lr}","X":["r3","r4"]},
            {"joker":6},
            {"instruction":"ubfx <X>,r0,#0x0,#0xf;ubfx r1,<X>,#0x4,#0x1","X":["r3","r0"]},
        ])
        for i in patterns.findPattern(self.firmware,patterns.generateAlternatives(pattern1,pattern2)):
            lculpCreateAccessAddress = i

        if lculpCreateAccessAddress is not None:
            return lculpCreateAccessAddress
        else:
            raise exceptions.AddressNotFound

    def extractConnectionTaskFunctions(self):
        # Find connTaskSlotInt address
        connTaskSlotIntAddress = None

        pattern1 = patterns.generatePattern([
            {"instruction":"push {r4,r5,r6,lr}"},
            {"instruction":"mov r4,r0"},
            {"instruction":"ldr r5,[r0,<X>]","X":["#0x50","#0x48", "#0x54"]},
            {"instruction":"ldrb.w r0,[r0,<X>]","X":["#0x79","#0x81", "#0x85"]}
        ])
        pattern2 = patterns.generatePattern([
        {"instruction":"ldrb.w <Y>,[r0,<X>]","X":["#0x79","#0x81"],"Y":["r1","r2","r3","r4"]},
        {"instruction":"push {r4,r5,r6,lr}"},
        {"instruction":"mov r4,r0"},
        ])
        for address in patterns.findPattern(self.firmware,patterns.generateAlternatives(pattern1,pattern2)):
            connTaskSlotIntAddress = address

        if connTaskSlotIntAddress is not None:
            # Find ROM Connection Task callbacks address
            candidates = [address for address in patterns.findPattern(self.firmware,patterns.generateFunctionPointerPattern(connTaskSlotIntAddress))]
            if len(candidates) == 0:

                connTaskRxHeaderDoneAddress = None
                pattern3 = patterns.generatePattern([
                {"instruction":"bic r0, r0, #0xff00"},
                {"instruction":"mov.w r2, #0xff00"},
                ])
                for address in patterns.findPattern(self.firmware,pattern3):
                    instructions = list(thumb.exploreInstructions(self.instructions[address-64:address]))
                    for instrIndex in range(len(instructions)-1):
                        if "push" in instructions[instrIndex] and "lr" in instructions[instrIndex]:
                            connTaskRxHeaderDoneAddress = thumb.extractInstructionAddress(instructions[instrIndex])
                            break

                connTaskRxDoneAddress = None
                pattern3 = patterns.generatePattern([
                {"instruction":"strh.w     r6,[r4,#0x8c]"},
                {"instruction":"strb.w     r6,[r4,#0x9d]"},
                ])
                for address in patterns.findPattern(self.firmware,pattern3):
                    instructions = list(thumb.exploreInstructions(self.instructions[address-64:address]))
                    for instrIndex in range(len(instructions)-1):
                        if "push" in instructions[instrIndex] and "lr" in instructions[instrIndex]:
                            connTaskRxDoneAddress = thumb.extractInstructionAddress(instructions[instrIndex])
                            break


                connTaskTxDoneAddress = None
                pattern3 = patterns.generatePattern([
                    {"instruction":"push {r4, r5, r6, r7, r8, r9, r10, lr}"},
                    {"instruction":"mov r4, r0"},
                    {"joker":2},
                    {"instruction":"adds r0, #0x44"},
                ])

                for address in patterns.findPattern(self.firmware,pattern3):
                    connTaskTxDoneAddress = address
                    break


                connTaskDeleteAddress = None
                pattern3 = patterns.generatePattern([
                    {"instruction":"movs r0, #0"}, #0x24"},
                    {"instruction":"bx lr"},
                    {"value":"24307047"},
                ])

                candidateList = [address for address in patterns.findPattern(self.firmware,pattern3)]
                if len(candidateList) > 0:
                    candidatesDict = {candidate:abs(connTaskTxDoneAddress - candidate) for candidate in candidateList}
                    minDistance = None
                    bestCandidate = None
                    for candidateAddress, distance in candidatesDict.items():
                        if minDistance is None or minDistance >= distance:
                            minDistance = distance
                            bestCandidate = candidateAddress
                    connTaskDeleteAddress = bestCandidate
                else:
                    connTaskDeleteAddress = None
                if connTaskDeleteAddress is not None and connTaskRxDoneAddress is not None and connTaskTxDoneAddress is not None and connTaskRxHeaderDoneAddress is not None and connTaskSlotIntAddress is not None:
                    return (connTaskDeleteAddress,connTaskRxDoneAddress,connTaskTxDoneAddress,connTaskRxHeaderDoneAddress, connTaskSlotIntAddress)
                else:
                    return exceptions.AddressNotFound

            if len(candidates) > 1:
                candidates = [candidate for candidate in candidates if candidate < self.firmwareStructure["rom"][1]] # if we got multiple candidates, select the ones in ROM
                set1 = set([self.firmware[candidate-12:candidate-8] for candidate in candidates])
                set2 = set([self.firmware[candidate-8:candidate-4] for candidate in candidates])
                set3 = set([self.firmware[candidate-4:candidate-0] for candidate in candidates])

                if len(set1) > 1:
                    set1 = set([max(set1)])

            if len(candidates) == 1 or (len(candidates) > 1 and len(set1) == 1 and len(set2) == 1 and len(set3) == 1):
                baseConnectionTaskAddressRom = candidates[0] - 36
                connTaskRxDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[baseConnectionTaskAddressRom+24:baseConnectionTaskAddressRom+28])
                connTaskTxDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[baseConnectionTaskAddressRom+28:baseConnectionTaskAddressRom+32])
                connTaskRxHeaderDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[baseConnectionTaskAddressRom+32:baseConnectionTaskAddressRom+36])
                connTaskSlotIntAddress = thumb.extractAddressFromFunctionPointer(self.firmware[baseConnectionTaskAddressRom+36:baseConnectionTaskAddressRom+40])

                connTaskDeleteAddress = thumb.extractAddressFromFunctionPointer(self.firmware[baseConnectionTaskAddressRom+8:baseConnectionTaskAddressRom+12])

                return (connTaskDeleteAddress,connTaskRxDoneAddress,connTaskTxDoneAddress,connTaskRxHeaderDoneAddress, connTaskSlotIntAddress)
            elif len(candidates) == 0:
                raise exceptions.AddressNotFound
            else:
                raise exceptions.MultipleCandidateAddresses
        else:
            raise exceptions.AddressNotFound

    def extractScanAndInitTaskFunctions(self):
        initTaskRxDoneAddress = None
        initTaskTxDoneAddress = None
        initTaskRxHeaderDoneAddress = None
        initTaskSlotIntAddress = None

        scanTaskRxDoneAddress = None
        scanTaskTxDoneAddress = None
        scanTaskRxHeaderDoneAddress = None
        scanTaskSlotIntAddress = None

        # Find scanTaskLcuSoftReset address
        scanTaskLcuSoftResetAddress = None
        pattern1 = patterns.generatePattern([
            {"instruction":"push {r4,lr}"},
            {"instruction":"mov r4,r0"},
            {"joker":4},
            {"instruction":"<X>","X":["lsls r1,r0,#0x1d","lsls r2,r0,#0x1d","tst r0,#4"]},
            {"joker":2},
            {"instruction":"ldr <X>,[r4,#0];ldr <X>,[<X>,#0x1c]","X":["r1","r2","r3","r4"]}
        ])
        for address in patterns.findPattern(self.firmware, pattern1):
            scanTaskLcuSoftResetAddress = address
        if scanTaskLcuSoftResetAddress is not None:
            # Find ROM Scan and/or Init Task callbacks address
            candidates = [address for address in patterns.findPattern(self.firmware,patterns.generateFunctionPointerPattern(scanTaskLcuSoftResetAddress))]
            for candidate in candidates:
                potentialInitTaskSlotIntAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+36:candidate+36+4])
                # Check if it is InitTaskSlotInt or ScanTaskSlotInt
                pattern2 = patterns.generatePattern([{"instruction":"blx <X>","X":["r0","r1","r2","r3"]}])
                if len(patterns.findPattern(self.firmware[potentialInitTaskSlotIntAddress:potentialInitTaskSlotIntAddress+128],pattern2)) > 0:
                    initTaskRxDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+24:candidate+24+4])
                    initTaskTxDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+28:candidate+28+4])
                    initTaskRxHeaderDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+32:candidate+32+4])
                    initTaskSlotIntAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+36:candidate+36+4])
                else:
                    scanTaskRxDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+24:candidate+24+4])
                    scanTaskTxDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+28:candidate+28+4])
                    scanTaskRxHeaderDoneAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+32:candidate+32+4])
                    scanTaskSlotIntAddress = thumb.extractAddressFromFunctionPointer(self.firmware[candidate+36:candidate+36+4])

            # We haven't found the Init table, try to find some functions independently...
            if initTaskRxHeaderDoneAddress is None:
                # find InitTaskSlotInt
                pattern3 = patterns.generatePattern([
                    {"instruction":"push {r4,lr}"},
                    {"instruction":"ldr r1,[r1,#0]"},
                    {"instruction":"mov r4,r0"},
                    {"instruction":"ldr r1,[r1,#0x24]"},

                ])
                for address in patterns.findPattern(self.firmware,pattern3):
                    initTaskSlotIntAddress = address-2

                # find InitTaskRxHeaderDone
                pattern4 = patterns.generatePattern([
                    {"instruction":"ldr <X>,[<Y>,#0]","X":["r1","r3"],"Y":["r0","r2"]},
                    {"instruction":"and<Z> <X>,<Y>,#0xf","Z":["","s"],"X":["r0","r3"],"Y":["r1","r3"]}
                ])

                for address in patterns.findPattern(self.firmware,pattern4):
                    disassembled =  self.instructions[address+6]
                    if "ubfx" in disassembled or "beq" in disassembled:
                        instructionAddress = address
                        pattern4 = patterns.generatePattern([
                            {"instruction":"push {r4,lr}"}
                        ])
                        for address in patterns.findPattern(self.firmware[instructionAddress-32:instructionAddress],pattern4):
                            initTaskRxHeaderDoneAddress = instructionAddress-32+address

            return (
                initTaskRxDoneAddress,
                initTaskTxDoneAddress,
                initTaskRxHeaderDoneAddress,
                initTaskSlotIntAddress,
                scanTaskRxDoneAddress,
                scanTaskTxDoneAddress,
                scanTaskRxHeaderDoneAddress,
                scanTaskSlotIntAddress
            )
        else:
            raise exceptions.AddressNotFound

    def extractScanTaskRxPacketUpdateFunction(self):
        scanTaskRxPktUpdateAddress = None

        pattern = patterns.generatePattern([
            {"instruction":"ubfx <X>,<Y>","X":["r1,r0","r0,r0","r3,r3"],"Y":["#1,#2","#2,#1"]},
        ])

        for address in patterns.findPattern(self.firmware,pattern):
            instructions = list(thumb.exploreInstructions(self.instructions[address-32:address+32]))
            for instrIndex in range(len(instructions)-2):
                if "push" in instructions[instrIndex] and "mov" in instructions[instrIndex+1] and "bl" in instructions[instrIndex+2] and "#3, #1" in "\n".join(instructions[instrIndex+2:]):
                    scanTaskRxPktUpdateAddress = thumb.extractInstructionAddress(instructions[instrIndex])

        if scanTaskRxPktUpdateAddress is not None:
            return scanTaskRxPktUpdateAddress
        else:
            raise exceptions.AddressNotFound

    def extractHciFunctions(self):
        allocateEventAndFillHeaderAddress = None
        attemptToEnqueueEventToTransportAddress = None

        if self.firmwareInformations["hci_implementation"] == "new":
            # We detect a function call to AllocateEventAndFillHeader
            pattern1 = patterns.generatePattern([
                {"instruction":"movs r1,#12"},
                {"instruction":"movs r0,#10"}
            ])
            pattern2 = patterns.generatePattern([
                {"instruction":"movs r0,#10"},
                {"instruction":"movs r1,#12"}
            ])

            candidatesAllocateEventAndFillHeaderAddresses = []
            candidatesAttemptToEnqueueEventToTransportAddresses = []

            for address in patterns.findPattern(self.firmware,patterns.generateAlternatives(pattern1,pattern2)):
                instructions = list(thumb.exploreInstructions(self.instructions[address+4:address+50]))

                # We extract the corresponding addresses from the next instructions
                for instruction in instructions:
                    if " bl " in instruction:
                        candidatesAllocateEventAndFillHeaderAddresses.append(thumb.extractTargetAddressFromJump(instruction))
                    elif " b." in instruction:
                        candidatesAttemptToEnqueueEventToTransportAddresses.append(thumb.extractTargetAddressFromJump(instruction))

            if len(set(candidatesAllocateEventAndFillHeaderAddresses)) == 1:
                allocateEventAndFillHeaderAddress = candidatesAllocateEventAndFillHeaderAddresses[0]
            elif len(set(candidatesAllocateEventAndFillHeaderAddresses)) == 0:
                raise exceptions.AddressNotFound
            else:
                raise exceptions.MultipleCandidateAddresses

            if len(set(candidatesAttemptToEnqueueEventToTransportAddresses)) == 1:
                attemptToEnqueueEventToTransportAddress = candidatesAttemptToEnqueueEventToTransportAddresses[0]
            elif len(set(candidatesAttemptToEnqueueEventToTransportAddresses)) == 0:
                raise exceptions.AddressNotFound
            else:
                raise exceptions.MultipleCandidateAddresses

            if allocateEventAndFillHeaderAddress is not None and attemptToEnqueueEventToTransportAddress is not None:
                return (allocateEventAndFillHeaderAddress,attemptToEnqueueEventToTransportAddress)
            else:
                raise exceptions.AddressNotFound
        else:
            allocateHciEventAddress = None
            sendHciEventAddress = None
            pattern1 = patterns.generatePattern([
                {"instruction":"push {r4-r6,lr}"},
                {"instruction":"mov r5,r0"},
                {"instruction":"mov r4,r1"},
                {"instruction":"adds r0,r1,#0x1"}
            ])

            pattern2 = patterns.generatePattern([
                {"instruction":"push {r4,r5,r6,lr}"},
                {"instruction":"ldrb r1,[r0,#1]"},
                {"instruction":"mov r5,r0"},

            ])

            for address in patterns.findPattern(self.firmware,pattern1):
                allocateHciEventAddress = address
                break
            for address in patterns.findPattern(self.firmware,pattern2):
                sendHciEventAddress = address
                break
            if sendHciEventAddress is not None and allocateHciEventAddress is not None:
                return (allocateHciEventAddress,sendHciEventAddress)
            else:
                raise exceptions.AddressNotFound

    def extractHciFreeEvent(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r4,lr}"},
            {"instruction":"bic r0,r0,#3"},
            {"joker":4},
            {"instruction":"cmp r0,#0"}
        ])

        freeHciEventAddress = None

        for address in patterns.findPattern(self.firmware,pattern):
            freeHciEventAddress = address

        if freeHciEventAddress is not None:
            return freeHciEventAddress
        else:
            raise exceptions.AddressNotFound

    def extractAdvTaskProgHw(self):
        advTaskProgHwAddress = None

        pattern = patterns.generatePattern([
            {"instruction":"orr r0,r0,#0x400040"}
        ])

        for address in patterns.findPattern(self.firmware, pattern):

            for instruction in list(thumb.exploreInstructions(self.instructions[address-512:address]))[::-1]:

                if "push" in instruction or "stmdb" in instruction:
                    advTaskProgHwAddress = thumb.extractInstructionAddress(instruction)
                    break
        if advTaskProgHwAddress is not None:
            return advTaskProgHwAddress
        else:
            raise exceptions.AddressNotFound

    def extractOsapiWaitEvent(self):
        osapiWaitEventAddress = None

        pattern1 = patterns.generatePattern([
            {"instruction":"strd r3,<X>,[sp,#0]","X":["r1","r5"]},
            {"instruction":"mov r4,r1"},
            {"instruction":"add r3,sp,#4"}

        ])
        pattern2 = patterns.generatePattern([
            {"instruction":"strd r3,<X>,[sp,#0]","X":["r1","r5"]},
            {"instruction":"add r3,sp,#4"},
            {"instruction":"mov r1,r4"},

        ])
        pattern3 = patterns.generatePattern([
            {"instruction":"str r6,[sp,#0xc]"},
            {"instruction":"add r6,sp,#0x10"},
            {"instruction":"movs r7,#0"},
        ])

        for address in patterns.findPattern(self.firmware, patterns.generateAlternatives(pattern1,pattern2,pattern3)):
            for instruction in list(thumb.exploreInstructions(self.instructions[address-512:address]))[::-1]:

                if "push" in instruction or "stmdb" in instruction:
                    osapiWaitEventAddress = thumb.extractInstructionAddress(instruction)
                    break
        if osapiWaitEventAddress is not None:
            return osapiWaitEventAddress
        else:
            raise exceptions.AddressNotFound


    def extractGetRawRssi(self):
        pattern1 = patterns.generatePattern([
            {"instruction":"add r0,r1"},
            {"instruction":"sxtb r0,r0"},
            {"instruction":"bx lr"},
        ])
        getRawRssiAddress = None

        for address in patterns.findPattern(self.firmware,pattern1):
            instructions = list(thumb.exploreInstructions(self.instructions[address-16:address]))[::-1]
            for instrIndex in range(len(instructions)-1):
                if "ldmia" in instructions[instrIndex+1] or "b." in instructions[instrIndex+1]:
                    getRawRssiAddress = thumb.extractInstructionAddress(instructions[instrIndex])
                    break

        if getRawRssiAddress is None:
            if "connTaskRxDone" not in self.functions:
                raise exceptions.AddressNotFound

            instructions = list(thumb.exploreInstructions(self.instructions[self.functions["connTaskRxDone"]:self.functions["connTaskRxDone"]+128]))
            for instrIndex in range(len(instructions)-2):
                if "bl" in instructions[instrIndex] and "strb" in instructions[instrIndex+1]:
                   getRawRssiAddress = thumb.extractTargetAddressFromJump(instructions[instrIndex])

        if getRawRssiAddress is not None:
            return getRawRssiAddress
        else:
            raise exceptions.AddressNotFound

    def extractHciCallbacksTable(self):
        callbackTableAddress = None
        if self.firmwareInformations["hci_implementation"] == "new":
            pattern = patterns.generatePattern([
                {"joker":4},
                {"value":"0b000600"},
                {"joker":4},
                {"value":"00000900"},
                {"joker":4},
                {"value":"00000e00"}
            ])
            for address in patterns.findPattern(self.firmware,pattern):
                callbackTableAddress = address
                break
            if callbackTableAddress is not None:
                return callbackTableAddress
            else:
                raise exceptions.AddressNotFound
        else:
            callbackTableAddress = None
            pattern = patterns.generatePattern([
                {"instruction":"ldrh.w r2,[r0,#1]"},
                {"instruction":"ubfx r2,r2,#0x0,#0xa"},

            ])
            for address in patterns.findPattern(self.firmware,pattern):
                instructions = list(thumb.exploreInstructions(self.instructions[address:address+16]))
                if "ldr" in instructions[-1]:
                    pointerToCallbackTable = thumb.extractTargetAddressFromLoadOrStore(instructions[-1])
                    callbackTableAddress = thumb.extractValue(self.firmware[pointerToCallbackTable:pointerToCallbackTable+4])

            if callbackTableAddress is not None:
                return callbackTableAddress
            else:
                raise exceptions.AddressNotFound


    def extractBdAddress(self):
        # First case
        pattern1 = patterns.generatePattern([
            {"instruction":"pop {r4,pc}"},
            {"joker":2},
            {"instruction":"ldr     r1, [r0, #0]"},
            {"instruction":"str.w   r1, [r2, #6]"},
            {"instruction":"ldrh    r0, [r0, #4]"},
            {"instruction":"strh    r0, [r2, #0xa]"},
        ])
        bdAddressPointer = None
        for i in patterns.findPattern(self.firmware,pattern1):
            address = thumb.extractTargetAddressFromLoadOrStore(self.instructions[i+2])
            bdAddressPointer = thumb.extractValue(self.firmware[address:address+4])
            break
        # Second case
        if bdAddressPointer is None:
            pattern2 = patterns.generatePattern([
                {"instruction":"push {r4,lr}"},
                {"instruction":"mov r4,r0"},
                {"instruction":"movs r2,#0x6"},
                {"joker":2},
                {"instruction":"adds r0,#0xe"},
                {"joker":4},
                {"instruction":"movs r0,#0x6"},
                {"instruction":"strb r0,[r4,#3]"},
                {"instruction":"pop {r4,pc}"},
                {"instruction":"push {r4,r5,r6,lr}"},
                {"instruction":"mov r5,r0"},
            ])


            for i in patterns.findPattern(self.firmware,pattern2):
                address = thumb.extractTargetAddressFromLoadOrStore(self.instructions[i+6])
                bdAddressPointer = struct.unpack("I", self.firmware[address:address+4])[0]
                break

        # Third case
        if bdAddressPointer is None:
            pattern3 = patterns.generatePattern([
                {"value":"012988bf01f0010131b138b1044b1b68984203d0"}, # pwnlib fails to disassemble the corresponding instructions
            ])


            for i in patterns.findPattern(self.firmware,pattern3):
                address = thumb.extractTargetAddressFromLoadOrStore(self.instructions[i+24])
                bdAddressPointer = thumb.extractValue(self.firmware[address:address+4])
        if bdAddressPointer is not None:
            return bdAddressPointer
        else:
            return exceptions.AddressNotFound

    def extractStatusRegister(self):
        if "scanTaskRxPktUpdate" not in self.functions:
            raise exceptions.AddressNotFound

        instructions = list(thumb.exploreInstructions(self.instructions[self.functions["scanTaskRxPktUpdate"]:self.functions["scanTaskRxPktUpdate"]+128]))

        loadingStatusRegisterInstructions = None
        for i in range(len(instructions)-3):
            if "bl" in instructions[i] and "ubfx" in instructions[i+3]:
                loadingStatusRegisterInstructions = instructions[i+1:i+3]
                break

        if loadingStatusRegisterInstructions is not None and len(loadingStatusRegisterInstructions) == 2:
            if "ldr" in loadingStatusRegisterInstructions[1]:
                if "ldr" in loadingStatusRegisterInstructions[0]:
                    pointerAddress = thumb.extractTargetAddressFromLoadOrStore(loadingStatusRegisterInstructions[0])
                    value = thumb.extractValue(self.firmware[pointerAddress:pointerAddress+4])
                    offsetValue = thumb.extractOffsetFromLoadOrStore(loadingStatusRegisterInstructions[1])

                elif "mov.w" in loadingStatusRegisterInstructions[0]:
                    value = thumb.extractOffsetFromLoadOrStore(loadingStatusRegisterInstructions[0])
                    offsetValue = thumb.extractOffsetFromLoadOrStore(loadingStatusRegisterInstructions[1])

                return value+offsetValue
        else:
            raise exceptions.AddressNotFound

    def extractRxHeaderRegister(self):
        rxHeaderRegister = None
        # if it has not been found previously, look for a matching set of instructions indicating this function
        if "initTaskRxHeaderDone" not in self.functions:
            raise exceptions.AddressNotFound

        instructions = list(thumb.exploreInstructions(self.instructions[self.functions["initTaskRxHeaderDone"]:self.functions["initTaskRxHeaderDone"]+32]))

        loadingRxHeaderRegisterInstructions = None

        for instrIndex in range(len(instructions)):
            if "and" in instructions[instrIndex] and "ldr" in instructions[instrIndex-1]:
                baseRegister = thumb.extractBaseRegisterFromLoadOrStore(instructions[instrIndex-1])
                offset = thumb.extractOffsetFromLoadOrStore(instructions[instrIndex-1])
                substract = 0
                for i in range(instrIndex-2,0,-1):
                    if baseRegister in instructions[i] and "subs" in instructions[i]:
                        substract = thumb.extractOffsetFromAddOrSub(instructions[i])
                    if baseRegister in instructions[i] and "ldr" in instructions[i] and "pc" in instructions[i]:
                        address = thumb.extractTargetAddressFromLoadOrStore(instructions[i])
                        rxHeaderRegister = thumb.extractValue(self.firmware[address:address+4]) - substract + offset
                        break

        if rxHeaderRegister is not None:
            return rxHeaderRegister
        else:
            raise exceptions.AddressNotFound

    def extractChannel(self):

        channelPointer = None
        pattern1 = patterns.generatePattern([
            {"instruction":"mov r1,r0"},
            {"joker":7},
            {"value":"e7"}
        ])

        pattern2 = patterns.generatePattern([
            {"instruction":"push {r4,lr}"},
            {"instruction":"mov r4,r0"},
        ])

        pattern3 = patterns.generatePattern([
            {"instruction":"pop.w {r4,lr}"},
            {"joker":2},
            {"instruction":"movs r0,#0x10"},
            {"joker":4},
            {"instruction":"ldrh.w r0,[r4,#9]"},
        ])

        # First method
        for address in patterns.findPattern(self.firmware,pattern1):
            instructions = list(thumb.exploreInstructions(self.instructions[address+2:address+10]))
            if "ldr" in instructions[0] and "pc" in instructions[0] and "strb.w" in instructions[1] and "r1" in instructions[1] and "b" in instructions[2]:
                basePointer = thumb.extractTargetAddressFromLoadOrStore(instructions[0])

                offset = thumb.extractOffsetFromLoadOrStore(instructions[1])
                channelPointer = thumb.extractValue(self.firmware[basePointer:basePointer+4]) + offset + 3

        # Second method
        if channelPointer is None:
            for address in patterns.findPattern(self.firmware,pattern2):
                instructions = list(thumb.exploreInstructions(self.instructions[address+4:address+16]))

                if "bl" in instructions[0] and "ldr" in instructions[1] and "strb.w" in instructions[2]:
                    basePointer = thumb.extractTargetAddressFromLoadOrStore(instructions[1])
                    offset = thumb.extractOffsetFromLoadOrStore(instructions[2])
                    channelPointer = thumb.extractValue(self.firmware[basePointer:basePointer+4]) + offset + 3

        # Third method
        if channelPointer is None:
            for address in patterns.findPattern(self.firmware,pattern3):
                instructions = list(thumb.exploreInstructions(self.instructions[address+2:address+6]))
                basePointer = thumb.extractTargetAddressFromLoadOrStore(instructions[0])
                scanTaskStorage = thumb.extractValue(self.firmware[basePointer:basePointer+4])

                channelPointer = scanTaskStorage + 0x56

        if channelPointer is not None:
            return channelPointer
        else:
            raise exceptions.AddressNotFound

    def extractRxRegister(self):
        rxRegister = None
        pattern = patterns.generatePattern([
            {"instruction":"ubfx r0,r0,#6,#1"},
            {"instruction":"<X>","X":["pop {r4,pc}","strb r0,[r2,#0]"]}
        ])


        for address in patterns.findPattern(self.firmware,pattern):
            instructions = list(thumb.exploreInstructions(self.instructions[address-32:address]))

            for instrIndex in range(len(instructions)):
                if "push" in instructions[instrIndex] or "ldmia" in instructions[instrIndex]:
                    instructions = instructions[instrIndex:]
                    break
            for instruction in instructions:
                if "ldr " in instruction and (";" in instruction or "@" in instruction):
                    addressPointer = thumb.extractTargetAddressFromLoadOrStore(instruction)
                    rxRegister = thumb.extractValue(self.firmware[addressPointer:addressPointer+4])
                    break

        if rxRegister is None:
            if "utils_memcpy8" not in self.functions or "scanTaskRxDone" not in self.functions:
                raise exceptions.AddressNotFound
            instructions = list(thumb.exploreInstructions(self.instructions[self.functions["scanTaskRxDone"]:self.functions["scanTaskRxDone"]+2048]))

            for instrIndex in range(len(instructions)):
                if "bl" in instructions[instrIndex] and hex(self.functions["utils_memcpy8"])[2:] in instructions[instrIndex]:
                    for instruction in instructions[instrIndex-8:instrIndex][::-1]:
                        if "ldr" in instruction and "r1" in instruction and "pc" in instruction and (";" in instruction or "@" in instruction):
                            addressPointer = thumb.extractTargetAddressFromLoadOrStore(instruction)
                            rxRegister = thumb.extractValue(self.firmware[addressPointer:addressPointer+4])

                            break
        if rxRegister is not None:
            return rxRegister
        else:
            raise exceptions.AddressNotFound


    def extractOffsetsInConnectionStructure(self):
        if "bcsulp_setupWhitening" not in self.functions or "lculp_createAccessAddress" not in self.functions or "connTaskRxHeaderDone" not in self.functions or "connTaskSlotInt" not in self.functions:
            raise exceptions.AddressNotFound

        pattern1 = patterns.generatePattern([
            {"instruction":"bic <X>,<X>,#0xff000000","X":["r0","r3"]},
        ])
        isSlaveOffsetInFirstStructure = None
        channelOffsetInFirstStructure = None
        offsetSecondStructure = None
        accessAddressOffsetInSecondStructure = None
        channelMapOffsetInSecondStructure = None
        crcInitOffsetInSecondStructure = None
        hopIntervalOffsetInSecondStructure = None

        for i in patterns.findPattern(self.firmware,pattern1):
            instructions = list(thumb.exploreInstructions(self.instructions[i-64:i+64]))

            for instruction in instructions:
                if "bl" in instruction and hex(self.functions["bcsulp_setupWhitening"])[2:] in instruction:
                    instructions2 = list(thumb.exploreInstructions(self.instructions[i-16:i+4]))
                    instructions3 = list(thumb.exploreInstructions(self.instructions[i-16:i+16]))

                    destRegister = thumb.extractDestRegisterFromBic(instructions2[-1])
                    initRegister = None

                    for instruction in instructions2[::-1]:

                        if "ldr" in instruction and "#0" in instruction and destRegister+"," in instruction and initRegister is None:
                            initRegister = thumb.extractBaseRegisterFromLoadOrStore(instruction)

                        if "ldr" in instruction and ";" in instruction and initRegister is not None and initRegister+"," in instruction:
                            offsetSecondStructure = thumb.extractOffsetFromLoadOrStore(instruction)
                            break
                    for instrIndex in range(len(instructions3)-2):
                        if ("ldr" in instructions3[instrIndex] and "bic" in instructions3[instrIndex+1]) or  ("ldr" in instructions3[instrIndex] and "add" in instructions3[instrIndex+1] and "bic" in instructions3[instrIndex+2]):
                            crcInitOffsetInSecondStructure = thumb.extractOffsetFromLoadOrStore(instructions3[instrIndex])
                            break
            for instrIndex in range(len(instructions)-2):
                if "ldrb.w" in instructions[instrIndex] and ";" in instructions[instrIndex] and "bl" in instructions[instrIndex+1] and hex(self.functions["bcsulp_setupWhitening"])[2:] in instructions[instrIndex+1]:
                    channelOffsetInFirstStructure = thumb.extractOffsetFromLoadOrStore(instructions[instrIndex])

        pattern2 = patterns.generatePattern([
            {"instruction":"bfi <X>,<Y>,#0,#5","X":["r0","r3"],"Y":["r0","r1"]}
        ])

        for address in patterns.findPattern(self.firmware,pattern2):
            instructions = list(thumb.exploreInstructions(self.instructions[address:address+64]))

            for instrIndex in range(len(instructions)):
                if "bl" in instructions[instrIndex] and hex(self.functions["lculp_createAccessAddress"])[2:] in instructions[instrIndex] and "str" in instructions[instrIndex+1] and ";" in instructions[instrIndex+1]:
                    accessAddressOffsetInSecondStructure = thumb.extractOffsetFromLoadOrStore(instructions[instrIndex+1])
                    break

            instructions = list(thumb.exploreInstructions(self.instructions[address-64:address]))[::-1]
            for instrIndex in range(len(instructions)-2):
                if "bl" in instructions[instrIndex] and "add" in instructions[instrIndex+1]:
                    channelMapOffsetInSecondStructure = thumb.extractOffsetFromAddOrSub(instructions[instrIndex+1])
                    break
                if "strb" in instructions[instrIndex] and "str" in instructions[instrIndex+2]:
                    channelMapOffsetInSecondStructure = thumb.extractOffsetFromLoadOrStore(instructions[instrIndex+2])
                    break

        instructions = list(thumb.exploreInstructions(self.instructions[self.functions["connTaskRxHeaderDone"]:self.functions["connTaskRxHeaderDone"]+128]))

        for instrIndex in range(len(instructions)-1):
            if "ldrb " in instructions[instrIndex] and "cmp" in instructions[instrIndex+1] and "#1" in instructions[instrIndex+1]:
                isSlaveOffsetInFirstStructure = thumb.extractOffsetFromLoadOrStore(instructions[instrIndex])
                break

        instructions = list(thumb.exploreInstructions(self.instructions[self.functions["connTaskSlotInt"]:self.functions["connTaskSlotInt"]+256]))
        for instrIndex in range(len(instructions)-1):
            if "ldrh " in instructions[instrIndex]:
                hopIntervalOffsetInSecondStructure = thumb.extractOffsetFromLoadOrStore(instructions[instrIndex])
                break
        if hopIntervalOffsetInSecondStructure is None: # if we were not able to found the offset, use the most probable hardcoded value
            hopIntervalOffsetInSecondStructure = 6 # offset found in every other firmware

        # default values if not found by disassembling code
        if isSlaveOffsetInFirstStructure is None:
            isSlaveOffsetInFirstStructure = 15
        if channelOffsetInFirstStructure is None:
            channelOffsetInFirstStructure = 123
        if offsetSecondStructure is None:
            offsetSecondStructure = 72
        if accessAddressOffsetInSecondStructure is None:
            accessAddressOffsetInSecondStructure = 40
        if crcInitOffsetInSecondStructure is None:
            crcInitOffsetInSecondStructure = 0
        if channelMapOffsetInSecondStructure is None:
            channelMapOffsetInSecondStructure = 12
        if hopIntervalOffsetInSecondStructure is None:
            hopIntervalOffsetInSecondStructure = 6
        #if isSlaveOffsetInFirstStructure is not None and channelOffsetInFirstStructure is not None and offsetSecondStructure is not None and accessAddressOffsetInSecondStructure is not None and channelMapOffsetInSecondStructure is not None:
        return (isSlaveOffsetInFirstStructure,
            channelOffsetInFirstStructure,
            offsetSecondStructure,
            crcInitOffsetInSecondStructure,
            hopIntervalOffsetInSecondStructure,
            accessAddressOffsetInSecondStructure,
            channelMapOffsetInSecondStructure)
        #else:
        #    raise exceptions.AddressNotFound

    def extractFunctions(self):
        try:
            self.functions["osapi_waitEvent"] = self.extractOsapiWaitEvent()
        except exceptions.AddressNotFound:
            print("osapi_waitEvent: function not found !")

        try:
            self.functions["advTaskProgHw"] = self.extractAdvTaskProgHw()
        except exceptions.AddressNotFound:
            print("advTaskProgHw: function not found !")

        try:
            self.functions["utils_memcpy8"] = self.extractUtilsMemcpy8()
        except exceptions.AddressNotFound:
            print("utils_memcpy8: function not found !")

        try:
            self.functions["__rt_memcpy"] = self.extractRtMemcpy()
        except exceptions.AddressNotFound:
            print("__rt_memcpy: function not found !")

        try:
            (
                self.functions["btclk_GetNatClk_clkpclk"],
                self.functions["btclk_Convert_clkpclk_us"]
            ) = self.extractTimestampFunctions()
        except exceptions.AddressNotFound:
            print("Timestamp functions: functions not found !")

        try:
            self.functions["bcsulp_setupWhitening"] = self.extractBcsulpSetupWhitening()
        except exceptions.AddressNotFound:
            print("bcsulp_setupWhitening: function not found !")

        try:
            self.functions["lculp_createAccessAddress"] = self.extractLculpCreateAccessAddress()
        except exceptions.AddressNotFound:
            print("lculp_createAccessAddress: function not found !")

        try:
            (
                self.functions["connTaskDelete"],
                self.functions["connTaskRxDone"],
                self.functions["connTaskTxDone"],
                self.functions["connTaskRxHeaderDone"],
                self.functions["connTaskSlotInt"]
            ) = self.extractConnectionTaskFunctions()
        except exceptions.AddressNotFound:
            print("ConnectionTask: functions not found !")
        except exceptions.MultipleCandidateAddresses:
            print("ConnectionTask: multiple candidates !")

        try:
            (
                self.functions["initTaskRxDone"],
                self.functions["initTaskTxDone"],
                self.functions["initTaskRxHeaderDone"],
                self.functions["initTaskSlotInt"],
                self.functions["scanTaskRxDone"],
                self.functions["scanTaskTxDone"],
                self.functions["scanTaskRxHeaderDone"],
                self.functions["scanTaskSlotInt"]
            ) = self.extractScanAndInitTaskFunctions()
        except exceptions.AddressNotFound:
            print("InitTask and ScanTask: functions not found !")
        except exceptions.MultipleCandidateAddresses:
            print("InitTask and ScanTask: multiple candidates !")

        try:
            self.functions["scanTaskRxPktUpdate"] = self.extractScanTaskRxPacketUpdateFunction()
        except exceptions.AddressNotFound:
            print("ScanTaskRxPktUpdate: function not found !")

        try:
            self.functions["lm_getRawRssiWithTaskId"] = self.extractGetRawRssi()
        except exceptions.AddressNotFound:
            print("lm_getRawRssiWithTaskId : function not found !")

        try:
            (
                self.functions["bthci_event_AllocateEventAndFillHeader"],
                self.functions["bthci_event_AttemptToEnqueueEventToTransport"]
            ) = self.extractHciFunctions()
        except exceptions.AddressNotFound:
            try:
                if self.firmwareInformations["hci_implementation"] == "old":
                    self.firmwareInformations["hci_implementation"] = "new"
                else:
                    self.firmwareInformations["hci_implementation"] = "old"
                (
                    self.functions["bthci_event_AllocateEventAndFillHeader"],
                    self.functions["bthci_event_AttemptToEnqueueEventToTransport"]
                ) = self.extractHciFunctions()
            except exceptions.AddressNotFound:
                print("HCI Functions: functions not found !")

            except exceptions.MultipleCandidateAddresses:
                print("HCI Functions: multiple candidates !")

        except exceptions.MultipleCandidateAddresses:
            print("HCI Functions: multiple candidates !")

        if self.firmwareInformations["hci_implementation"] == "old":
            try:
                self.functions["bthci_event_FreeEvent"] = self.extractHciFreeEvent()
            except exceptions.AddressNotFound:
                print("HCI Free event function: function not found !")

    def extractDatas(self):
        try:
            self.datas["hci_callbacks_table"] = self.extractHciCallbacksTable()
        except exceptions.AddressNotFound:
            print("HCI Callbacks table: address not found !")

        try:
            self.datas["bd_address"] = self.extractBdAddress()
        except exceptions.AddressNotFound:
            print("BD Address pointer: address not found !")

        try:
            self.datas["status_register"] = self.extractStatusRegister()
        except exceptions.AddressNotFound:
            print("Status register: address not found !")

        try:
            self.datas["rx_header_register"] = self.extractRxHeaderRegister()
        except exceptions.AddressNotFound:
            print("RX Header register: address not found !")

        try:
            self.datas["channel"] = self.extractChannel()
        except exceptions.AddressNotFound:
            print("Channel: address not found !")

        try:
            self.datas["rx_register"] = self.extractRxRegister()
        except exceptions.AddressNotFound:
            print("RX register: address not found !")

        try:
            (
                self.datas["is_slave_offset"],
                self.datas["channel_offset"],
                self.datas["second_struct_offset"],
                self.datas["crc_init_offset"],
                self.datas["hop_interval_offset"],
                self.datas["access_address_offset"],
                self.datas["channel_map_offset"],

            ) = self.extractOffsetsInConnectionStructure()

        except exceptions.AddressNotFound:
            print("Connection offsets: values not found !")

    def generateCapabilities(self):
        self.firmwareInformations["scanner"] = "scanTaskRxDone" in self.functions
        self.firmwareInformations["peripheral"] = "connTaskRxDone" in self.functions
        self.firmwareInformations["central"] = "connTaskRxDone" in self.functions
        self.firmwareInformations["advertiser"] = "advTaskProgHw" in self.functions
        self.firmwareInformations["hci_support"] = "bthci_event_AllocateEventAndFillHeader" in self.functions

    def findPatchableInstruction(self,function,size=32):
        twoBytesInstructions = []
        for instruction in thumb.exploreInstructions(self.instructions[self.functions[function]:self.functions[function]+size]):
            code = bytes.fromhex(instruction.split("       ")[1])
            if len(twoBytesInstructions) != 0 and len(code) == 2 and "sp" not in instruction and "pc" not in instruction and "lr" not in instruction:
                twoBytesInstructions.append(instruction)
                return twoBytesInstructions
            else:
                if len(code) == 2 and "sp" not in instruction and "pc" not in instruction and "lr" not in instruction:
                    twoBytesInstructions = [instruction]
                else:
                    twoBytesInstructions = []
            if len(code) == 4 and "lr" not in instruction and "pc" not in instruction and "sp" not in instruction:
                return instruction

            elif len(code) == 2 and "lr" not in instruction and "pc" not in instruction and "sp" not in instruction and function == "osapi_waitEvent" and self.firmwareInformations["hci_implementation"] == "new":
                twoBytesInstructions.append(instruction)


    def generatePatches(self):
        out = ""
        patchesList = {
            "scanTaskRxHeaderDone" : ("on_scan_rx_header","SCAN"),
            "scanTaskRxDone" : ("on_scan_rx","SCAN"),
            "connTaskRxHeaderDone" : ("on_conn_rx_header","CONNECTION"),
            "connTaskRxDone" : ("on_conn_rx","CONNECTION"),
            "connTaskDelete" : ("on_conn_delete","CONNECTION"),
            "advTaskProgHw" : ("on_adv_setup","COMMON"),
            "osapi_waitEvent" : ("on_event_loop","COMMON")
        }
        for functionName,(targetName,dependency) in patchesList.items():
            instruction = self.findPatchableInstruction(functionName)
            if isinstance(instruction,list):
                address = thumb.extractInstructionAddress(instruction[0])
                instructionToReplace = thumb.extractTextFromInstruction(instruction[0])+";"+thumb.extractTextFromInstruction(instruction[1])
            else:
                address = thumb.extractInstructionAddress(instruction)
                instructionToReplace = thumb.extractTextFromInstruction(instruction)
            out += patch_generator.generateFunctionHookPatch(dependency, "rom", "hook_"+targetName, address, targetName, instructionToReplace)

        return out

    def generateUsedFunctions(self):
        functions = {
            "__rt_memcpy":("void *","void * dst, void * src, uint32_t size"),
            "utils_memcpy8":("void *","void * dst, void * src, uint32_t size"),
            "btclk_GetNatClk_clkpclk":("void","uint32_t * t"),
            "btclk_Convert_clkpclk_us":("uint32_t","uint32_t *p"),
             "lm_getRawRssiWithTaskId":("int","")
         }
        if self.firmwareInformations["hci_implementation"] == "new":
            functions.update({
                "bthci_event_AllocateEventAndFillHeader":("char *","uint8_t len_total, char event_code, uint8_t len_data"),
                "bthci_event_AttemptToEnqueueEventToTransport":("void","char *event"),
            })
        else:
            functions.update({
                "bthci_event_AllocateEventAndFillHeader":("char *","char event_code, uint8_t len_total"),
                "bthci_event_AttemptToEnqueueEventToTransport":("void","char *event"),
                "bthci_event_FreeEvent":("void","char *event")
            })

        self.firmwareInformations["used_functions"] = functions


    def generateLinkerScripts(self):
        functionsOut = ""
        self.generateUsedFunctions()

        functionsOut += linker_generator.generateFunctions({k:v for k,v in self.functions.items() if k in self.firmwareInformations["used_functions"].keys()})
        linkerOut = linker_generator.generateMemoryZonesAndSections()
        return functionsOut,linkerOut

    def generateWrapper(self):
        wrapperOut = ""
        wrapperOut += wrapper_generator.generateIncludes()+"\n"

        wrapperOut += wrapper_generator.generateComment("Offsets used in connection structure")
        offsets = {k:v for k,v in self.datas.items() if "offset" in k}
        wrapperOut += wrapper_generator.generateBroadcomWrapperHeader(offsets)

        wrapperOut += wrapper_generator.generateComment("Controller functions used by the wrapper")+"\n"
        for function,(returnValue,parameters) in self.firmwareInformations["used_functions"].items():
            wrapperOut += wrapper_generator.generateFunctionSignature(function,returnValue, parameters)+"\n"

        wrapperOut += wrapper_generator.generateComment("Hardware registers and variables used by the wrapper")
        registers = {k:hex(v) for k,v in self.datas.items() if "offset" not in k}
        wrapperOut += wrapper_generator.generateBroadcomWrapperRegisters(registers)

        wrapperOut += wrapper_generator.generateComment("Global variables used internally by the wrapper")
        wrapperOut += wrapper_generator.generateBroacomWrapperGlobalsVariables()

        wrapperOut += wrapper_generator.generateComment("Generic Wrapper API")
        wrapperOut += wrapper_generator.generateBroadcomGenericAPI()

        wrapperOut += wrapper_generator.generateComment("Host-Controller Interface API")
        if self.firmwareInformations["hci_implementation"] == "old":
            wrapperOut += wrapper_generator.generateBroadcomOldHciAPI()
        else:
            wrapperOut += wrapper_generator.generateBroadcomNewHciAPI()

        wrapperOut += wrapper_generator.generateComment("Actions API")
        wrapperOut += wrapper_generator.generateBroadcomWrapperActionsAPI()

        wrapperOut += wrapper_generator.generateComment("Hooks")
        wrapperOut += wrapper_generator.generateBroadcomWrapperHooks()
        return wrapperOut

    def generateConfiguration(self):
        configuration = ""
        if self.memoryZones["code_start"] is None or self.memoryZones["data_start"] is None:
            freeZone = None
            interface = InternalblueInterface(None, self.interfaceType,self.firmwareStructure)
            if not interface.checkSupport("FIND_MEMORY_ZONE"):
                print("Interface does not support memory zone finding.")
                exit(1)
            interface.connect()
            freeZone = interface.findFreeZone(self.memoryZones["code_size"]+self.memoryZones["data_size"],strategy=self.memoryZones["strategy"])
            interface.disconnect()
            if freeZone is None:
                print("No zone found, impossible to generate configuration file !")
                exit(1)
            else:
                self.memoryZones["code_start"] = freeZone
                self.memoryZones["data_start"] = freeZone + self.memoryZones["code_size"]

        capabilities = {i:self.firmwareInformations[i] for i in Controller.CAPABILITIES}
        configuration = conf_generator.generateConfiguration(self.name,capabilities, self.memoryZones["code_start"],self.memoryZones["code_size"], self.memoryZones["data_start"],self.memoryZones["data_size"],self.heapSize, self.firmwareStructure, self.interfaceType, self.firmwareInformations["architecture"], self.firmwareInformations["file_type"])
        return configuration
