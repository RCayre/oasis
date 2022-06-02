from oasis.controllers.controller import Controller
from oasis.controllers.analysis import hextools,patterns,thumb,exceptions
from oasis.controllers.generators import patch_generator,linker_generator,wrapper_generator,conf_generator
import struct

class NRF52ZephyrController(Controller):
    startOffset = None
    codeSegment = None
    instructionPointer = None

    def __init__(self,filename):
        self.firmwarePath = filename
        self.startOffset,firmware,self.codeSegment,self.instructionPointer = hextools.hexToInternal(filename)
        if self.startOffset > 0:
            firmware = self.startOffset*b"\x00" + firmware
        Controller.__init__(self,firmware)

    def extractFirmwareStructure(self):
        stackPointer = struct.unpack('I',self.firmware[self.startOffset:self.startOffset+4])[0]
        self.firmwareStructure["rom"] = (self.startOffset,len(self.firmware)-self.startOffset)
        self.firmwareStructure["ram"] = (0x20000000,self.startOffset)
        self.firmwareStructure["ram_used"] = (0x20000000,0x20010000)
        self.firmwareInformations["isr_vector"] = self.startOffset


    def extractFirmwareInformations(self):
        self.firmwareInformations["architecture"] = "armv7-m"
        self.firmwareInformations["gcc_flags"] = "-DALIGNED_MALLOC -mno-unaligned-access"
        self.firmwareInformations["file_type"] = "hex"

    def extractZArmReset(self):
        pattern = patterns.generatePattern([
            {"joker":4},
            {"instruction":"movs r0,#0x20"},
            {"value":"80f31188"},
            {"joker":2},
            {"instruction":"mov.w r1,#0x820"},
            {"instruction":"adds r0,r0,r1"},

        ])

        zArmResetAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            zArmResetAddress = i
            break
        if zArmResetAddress is not None:
            return zArmResetAddress
        else:
            raise exceptions.AddressNotFound

    def extractZArmConfigureStaticMpuRegions(self):
        pattern = patterns.generatePattern([
            {"value":"024b034a0348"},
            {"instruction":"movs r1,#1"}

        ])

        zArmConfigureStaticMpuRegionsAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            zArmConfigureStaticMpuRegionsAddress = i
            break
        if zArmConfigureStaticMpuRegionsAddress is not None:
            return zArmConfigureStaticMpuRegionsAddress
        else:
            raise exceptions.AddressNotFound

    def extractMemcpy(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r4,lr}"},
            {"instruction":"subs r3,r0,#1"},
            {"instruction":"add r2,r1"}
        ])
        memcpyAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            memcpyAddress = i
            break

        if memcpyAddress is not None:
            return memcpyAddress
        else:
            raise exceptions.AddressNotFound

    def extractRadioIsDone(self):
        pattern = patterns.generatePattern([
            {"value":"034b"},
            {"instruction":"ldr.w r0,[r3,#0x10c]"},
            {"instruction":"subs r0,#0"}
        ])
        radioIsDoneAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            radioIsDoneAddress = i
            break

        if radioIsDoneAddress is not None:
            return radioIsDoneAddress
        else:
            raise exceptions.AddressNotFound


    def extractRadioCrcIsValid(self):
        pattern = patterns.generatePattern([
            {"value":"034b"},
            {"instruction":"ldr.w r0,[r3,#0x400]"},
            {"instruction":"subs r0,#0"}
        ])
        radioCrcIsValidAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            radioCrcIsValidAddress = i
            break

        if radioCrcIsValidAddress is not None:
            return radioCrcIsValidAddress
        else:
            raise exceptions.AddressNotFound

    def extractRadioRssiGet(self):
        pattern = patterns.generatePattern([
            {"value":"014b"},
            {"instruction":"ldr.w r0,[r3,#0x548]"},
            {"instruction":"bx lr"},
            {"value":"00100040"}
        ])
        radioRssiGetAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            radioRssiGetAddress = i
            break

        if radioRssiGetAddress is not None:
            return radioRssiGetAddress
        else:
            raise exceptions.AddressNotFound


    def extractLllAdvScanReqCheck(self):
        pattern1 = patterns.generatePattern([
            {"instruction":"push {r3-r9,lr}"},
            {"instruction":"mov r6,r3"},
            {"instruction":"ldrb r3,[r0,#4]"}
        ])
        pattern2 = patterns.generatePattern([
            {"instruction":"push {r4-r8,lr}"},
            {"instruction":"ldrb.w r12,[r0,#9]"},
            {"instruction":"ldrb.w r8,[sp,#24]"}
        ])
        lllAdvScanReqCheckAddress = None
        for i in patterns.findPattern(self.firmware,patterns.generateAlternatives(pattern1,pattern2)):
            lllAdvScanReqCheckAddress = i
            break

        if lllAdvScanReqCheckAddress is not None:
            return lllAdvScanReqCheckAddress
        else:
            raise exceptions.AddressNotFound

    def extractLllScanPrepareConnectReq(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r4-r8,lr}"},
            {"instruction":"ldrb.w r5,[sp,#28]"}
        ])
        lllScanPrepareConnectReqAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            lllScanPrepareConnectReqAddress = i
            break

        if lllScanPrepareConnectReqAddress is not None:
            return lllScanPrepareConnectReqAddress
        else:
            raise exceptions.AddressNotFound

    def extractLllScanIsrRxCheck(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r4,lr}"},
            {"instruction":"mov r4,r0"},
            {"instruction":"mov r0,r1"},
            {"instruction":"mov r1,r3"},
            {"instruction":"ldrb r3,[r4,#0x4]"},
        ])
        lllScanIsrRxCheckAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            lllScanIsrRxCheckAddress = i
            break

        if lllScanIsrRxCheckAddress is not None:
            return lllScanIsrRxCheckAddress
        else:
            raise exceptions.AddressNotFound


    def extractLllConnPduPrepareTx(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r4-r9,lr}"},
            {"instruction":"mov r4,r0"},
            {"instruction":"sub sp,#0xc"},
            {"instruction":"add r2,sp,#4"}
        ])
        lllConnPduPrepareTxAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            lllConnPduPrepareTxAddress = i
            break

        if lllConnPduPrepareTxAddress is not None:
            return lllConnPduPrepareTxAddress
        else:
            raise exceptions.AddressNotFound

    def extractIsrRx(self):

        if "radio_is_done" not in self.functions:
            raise exceptions.AddressNotFound

        advertiserRxIsr = None
        scannerRxIsr = None
        connectionRxIsr = None
        testRxIsr = None

        rxIsrs = []
        for i in thumb.findReferences(self.instructions, self.functions["radio_is_done"]):
            instructions = list(thumb.exploreInstructions(self.instructions[i-256:i]))[::-1]
            for instruction in instructions:
                if ("push" in instruction or "stmdb" in instruction) and "lr" in instruction:
                    rxIsrs.append(thumb.extractInstructionAddress(instruction))
                    break
        if "lll_adv_scan_req_check" in self.functions:
            for i in thumb.findReferences(self.instructions, self.functions["lll_adv_scan_req_check"]):
                instructions = list(thumb.exploreInstructions(self.instructions[i-512:i]))[::-1]
                for instruction in instructions:
                    if ("push" in instruction or "stmdb" in instruction) and "lr" in instruction and thumb.extractInstructionAddress(instruction) in rxIsrs:
                        advertiserRxIsr = thumb.extractInstructionAddress(instruction)
                        break

        if "lll_scan_prepare_connect_req" in self.functions:
            for i in thumb.findReferences(self.instructions, self.functions["lll_scan_prepare_connect_req"]):
                instructions = list(thumb.exploreInstructions(self.instructions[i-1024:i]))[::-1]
                for instruction in instructions:
                    if ("push" in instruction or "stmdb" in instruction) and "lr" in instruction and thumb.extractInstructionAddress(instruction) in rxIsrs:
                        scannerRxIsr = thumb.extractInstructionAddress(instruction)
                        break
        if scannerRxIsr is None and "lll_scan_isr_rx_check" in self.functions:
            for i in thumb.findReferences(self.instructions, self.functions["lll_scan_isr_rx_check"]):
                instructions = list(thumb.exploreInstructions(self.instructions[i-1024:i]))[::-1]
                for instruction in instructions:
                    if ("push" in instruction or "stmdb" in instruction) and "lr" in instruction and thumb.extractInstructionAddress(instruction) in rxIsrs:
                        scannerRxIsr = thumb.extractInstructionAddress(instruction)
                        break


        if "lll_conn_prepare_pdu_tx" in self.functions:
            for i in thumb.findReferences(self.instructions, self.functions["lll_conn_prepare_pdu_tx"]):
                instructions = list(thumb.exploreInstructions(self.instructions[i-512:i]))[::-1]
                for instruction in instructions:
                    if ("push" in instruction or "stmdb" in instruction) and "lr" in instruction  and thumb.extractInstructionAddress(instruction) in rxIsrs:
                        connectionRxIsr = thumb.extractInstructionAddress(instruction)
                        break

        for isr in rxIsrs:
            if isr != advertiserRxIsr and isr != scannerRxIsr and isr != connectionRxIsr:
                testRxIsr = isr
                break

        return (advertiserRxIsr,scannerRxIsr,connectionRxIsr,testRxIsr)

    def extractConnIsrTx(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r3-r5,lr}"},
            {"instruction":"mov r4,r0"},
            {"joker":4},
            {"instruction":"movs r0,#0x96"},
        ])
        connIsrTxAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            connIsrTxAddress = i
            break

        if connIsrTxAddress is not None:
            return connIsrTxAddress
        else:
            raise exceptions.AddressNotFound

    def extractUllCentralSetup(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r4-r11,lr}"},
            {"instruction":"<X>","X":["mov r8,r0",""]},
            {"instruction":"sub sp,#0x3c"},
            {"instruction":"mov r4,r0"},
        ])
        ullCentralSetupAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            ullCentralSetupAddress = i
            break

        if ullCentralSetupAddress is not None:
            return ullCentralSetupAddress
        else:
            raise exceptions.AddressNotFound

    def extractUllCentralCleanup(self):
        pattern = patterns.generatePattern([
            {"instruction":"ldr r3,[r0,#8]"},
            {"instruction":"push {r4-r6,lr}"},
            {"instruction":"ldr r5,[r3,#0]"},
            {"instruction":"ldr r4,[r5,#0x20]"},
        ])
        ullCentralCleanupAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            ullCentralCleanupAddress = i
            break

        if ullCentralCleanupAddress is not None:
            return ullCentralCleanupAddress
        else:
            raise exceptions.AddressNotFound


    def extractIdleThread(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r3,lr}"},
            {"value":"094c"},
            {"instruction":"mov.w r2,#0x20"}
        ])
        idleThreadAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            idleThreadAddress = i
            break

        if idleThreadAddress is not None:
            return idleThreadAddress
        else:
            raise exceptions.AddressNotFound



    def extractUllPeripheralSetup(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r4-r11,lr}"},
            {"instruction":"ldr r3,[r1,#0]"},
            {"instruction":"ldr.w <X>,[r2]","X":["r8","r11","r10"]},
            {"instruction":"ldr r3,[r3,#0]"},
        ])
        ullPeripheralSetupAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            ullPeripheralSetupAddress = i
            break

        if ullPeripheralSetupAddress is not None:
            return ullPeripheralSetupAddress
        else:
            raise exceptions.AddressNotFound

    def extractBtEnableRaw(self):
        pattern = patterns.generatePattern([
            {"value":"044b054a"},
            {"instruction":"ldr r3,[r3,#0]"}
        ])
        btEnableRawAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            btEnableRawAddress  = i
            break

        if btEnableRawAddress is not None:
            return btEnableRawAddress
        else:
            raise exceptions.AddressNotFound

    def extractBtRecv(self):
        pattern1 = patterns.generatePattern([
            {"instruction":"push {r4,lr}"},
            {"value":"0d4b"},
            {"instruction":"ldrb r3,[r3,#0]"}
        ])

        pattern2 = patterns.generatePattern([
            {"instruction":"push {r3,lr}"},
            {"value":"034b"},
            {"instruction":"mov r1,r0"},
            {"instruction":"ldr r0,[r3,#0]"}
        ])
        btRecvAddress = None
        for i in patterns.findPattern(self.firmware,patterns.generateAlternatives(pattern1,pattern2)):
            btRecvAddress  = i
            break

        if btRecvAddress is not None:
            return btRecvAddress
        else:
            raise exceptions.AddressNotFound

    def extractBtSend(self):
        pattern = patterns.generatePattern([
            {"joker":1},
            {"value":"4b"},
            {"instruction":"ldr r3,[r3,#<X>]","X":["0","276","332"]},
            {"instruction":"ldr r3,[r3,#0x10]"},
            {"instruction":"bx r3"}
        ])

        btSendAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            btSendAddress  = i
            break

        if btSendAddress is not None:
            return btSendAddress
        else:
            raise exceptions.AddressNotFound


    def extractBtHciEvtCreate(self):
        pattern = patterns.generatePattern([
            {"instruction":"push {r4-r6,lr}"},
            {"instruction":"mov.w r2,#0xffffffff"},
            {"instruction":"mov r5,r1"},
            {"instruction":"mov.w r3,#0xffffffff"},
            {"instruction":"movs r1,#0"},
        ])
        btHciEvtCreateAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            btHciEvtCreateAddress  = i
            break

        if btHciEvtCreateAddress is not None:
            return btHciEvtCreateAddress
        else:
            raise exceptions.AddressNotFound

    def extractNetBufSimpleAdd(self):
        pattern = patterns.generatePattern([
            {"instruction":"ldrh r3,[r0,#4]"},
            {"instruction":"ldr r2,[r0,#0]"},
            {"instruction":"add r1,r3"},
            {"instruction":"strh r1,[r0,#4]"},
            {"instruction":"adds r0,r2,r3"},
            {"instruction":"bx lr"},
        ])
        netBufSimpleAddAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            netBufSimpleAddAddress  = i
            break

        if netBufSimpleAddAddress is not None:
            return netBufSimpleAddAddress
        else:
            raise exceptions.AddressNotFound

    def extractllAddrGet(self):
        pattern = patterns.generatePattern([
            {"instruction":"cmp r0,#0x1"},
            {"instruction":"<X>","X":["push {r3,lr}",""]},
            {"instruction":"mov <X>,r0","X":["r3","r2"]},

        ])
        llAddrGetAddress = None
        for i in patterns.findPattern(self.firmware,pattern):
            llAddrGetAddress  = i
            break

        if llAddrGetAddress is not None:
            return llAddrGetAddress
        else:
            raise exceptions.AddressNotFound

    def extractMaxRamAddress(self):
        if "z_arm_configure_static_mpu_regions" not in self.functions:
            raise exceptions.AddressNotFound

        baseAddress = self.functions["z_arm_configure_static_mpu_regions"]
        instructions = list(thumb.exploreInstructions(self.instructions[baseAddress:baseAddress+16]))
        maxRamAddressPointer = thumb.extractTargetAddressFromLoadOrStore(instructions[0])
        maxRamAddress = struct.unpack("I",self.firmware[maxRamAddressPointer:maxRamAddressPointer+4])[0]
        return maxRamAddressPointer,maxRamAddress


    def extractFunctions(self):
        try:
            self.functions["z_arm_reset"] = self.extractZArmReset()
        except exceptions.AddressNotFound:
            print("z_arm_reset: function not found !")
        try:
            self.functions["z_arm_configure_static_mpu_regions"] = self.extractZArmConfigureStaticMpuRegions()
        except exceptions.AddressNotFound:
            print("z_arm_configure_static_mpu_regions: function not found !")
        try:
            self.functions["memcpy"] = self.extractMemcpy()
        except exceptions.AddressNotFound:
            print("memcpy: function not found !")
        try:
            self.functions["radio_is_done"] = self.extractRadioIsDone()
        except exceptions.AddressNotFound:
            print("radio_is_done: function not found !")

        try:
            self.functions["radio_rssi_get"] = self.extractRadioRssiGet()
        except exceptions.AddressNotFound:
            print("radio_rssi_get: function not found !")

        try:
            self.functions["radio_crc_is_valid"] = self.extractRadioCrcIsValid()
        except exceptions.AddressNotFound:
            print("radio_crc_is_valid: function not found !")

        try:
            self.functions["lll_adv_scan_req_check"] = self.extractLllAdvScanReqCheck()
        except exceptions.AddressNotFound:
            print("lll_adv_scan_req_check: function not found !")

        try:
            self.functions["lll_scan_prepare_connect_req"] = self.extractLllScanPrepareConnectReq()
        except exceptions.AddressNotFound:
            print("lll_scan_prepare_connect_req: function not found !")

        try:
            self.functions["lll_scan_isr_rx_check"] = self.extractLllScanIsrRxCheck()
        except exceptions.AddressNotFound:
            print("lll_scan_isr_rx_check: function not found !")
        try:
            self.functions["lll_conn_prepare_pdu_tx"] = self.extractLllConnPduPrepareTx()
        except exceptions.AddressNotFound:
            print("lll_conn_prepare_pdu_tx: function not found !")

        try:
            (
                self.functions["advertiser_isr_rx"],
                self.functions["scan_isr_rx"],
                self.functions["conn_isr_rx"],
                self.functions["test_isr_rx"]
            ) = self.extractIsrRx()

        except exceptions.AddressNotFound:
            print("rx_isr: functions not found !")

        if "conn_isr_rx" in self.functions:
            try:
                self.functions["conn_isr_tx"] = self.extractConnIsrTx()
            except exceptions.AddressNotFound:
                print("conn_isr_tx: function not found !")

        try:
            self.functions["ull_central_setup"] = self.extractUllCentralSetup()
        except exceptions.AddressNotFound:
            print("ull_central_setup: function not found !")


        try:
            self.functions["ull_central_cleanup"] = self.extractUllCentralCleanup()
        except exceptions.AddressNotFound:
            print("ull_central_cleanup: function not found !")


        try:
            self.functions["ull_peripheral_setup"] = self.extractUllPeripheralSetup()
        except exceptions.AddressNotFound:
            print("ull_peripheral_setup: function not found !")

        try:
            self.functions["bt_enable_raw"] = self.extractBtEnableRaw()
        except exceptions.AddressNotFound:
            print("bt_enable_raw: function not found !")

        try:
            self.functions["bt_recv"] = self.extractBtRecv()
        except exceptions.AddressNotFound:
            print("bt_recv: function not found !")

        try:
            self.functions["bt_send"] = self.extractBtSend()
        except exceptions.AddressNotFound:
            print("bt_send: function not found !")
        try:
            self.functions["bt_hci_evt_create"] = self.extractBtHciEvtCreate()
        except exceptions.AddressNotFound:
            print("bt_hci_evt_create: function not found !")

        try:
            self.functions["net_buf_simple_add"] = self.extractNetBufSimpleAdd()
        except exceptions.AddressNotFound:
            print("net_buf_simple_add: function not found !")

        try:
            self.functions["ll_addr_get"] = self.extractllAddrGet()
        except exceptions.AddressNotFound:
            print("ll_addr_get: function not found !")

        try:
            self.functions["idle"] = self.extractIdleThread()
        except exceptions.AddressNotFound:
            print("idle: function not found !")

    def generateCapabilities(self):
        self.firmwareInformations["scanner"] = "scan_isr_rx" in self.functions and self.functions["scan_isr_rx"] is not None
        self.firmwareInformations["peripheral"] = "conn_isr_rx" in self.functions and "ull_peripheral_setup" in self.functions and self.functions["conn_isr_rx"] is not None  and self.functions["ull_peripheral_setup"] is not None
        self.firmwareInformations["central"] = "conn_isr_rx" in self.functions and "ull_central_setup" in self.functions and self.functions["conn_isr_rx"] is not None and self.functions["ull_central_setup"] is not None
        self.firmwareInformations["advertiser"] = "advertiser_isr_rx" in self.functions and self.functions["advertiser_isr_rx"] is not None
        self.firmwareInformations["hci_support"] = "bt_enable_raw" in self.functions and self.functions["bt_enable_raw"] is not None

    def extractDatas(self):
        try:
            self.datas["max_ram_address_pointer"],self.datas["max_ram_address"] = self.extractMaxRamAddress()
        except exceptions.AddressNotFound:
            print("max_ram_address: value & pointer not found !")


    def findPatchableInstruction(self,function,size=30):
        twoBytesInstructions = []
        for instruction in thumb.exploreInstructions(self.instructions[self.functions[function]:self.functions[function]+size]):
            code = bytes.fromhex(instruction.split("       ")[1])
            if len(twoBytesInstructions) != 0 and len(code) == 2 and "sp" not in instruction and "pc" not in instruction and "lr" not in instruction:
                twoBytesInstructions.append(instruction)
                return twoBytesInstructions
            else:
                twoBytesInstructions = []
            if len(code) == 4 and "lr" not in instruction and "pc" not in instruction and "sp" not in instruction:
                return instruction

            elif len(code) == 2 and "lr" not in instruction and "pc" not in instruction and "sp" not in instruction and function == "osapi_waitEvent" and self.firmwareInformations["hci_implementation"] == "new":
                twoBytesInstructions.append(instruction)


    def generatePatches(self):
        out = ""
        patchesList = {
            "z_arm_reset" : ("on_init","COMMON"),
            "idle" : ("on_event_loop","COMMON"),
        }
        if self.firmwareInformations["scanner"]:
            patchesList.update({
                                "scan_isr_rx" : ("on_scan","SCAN")
            })
        if self.firmwareInformations["central"] or self.firmwareInformations["peripheral"]:
            patchesList.update({
                                "conn_isr_rx" : ("on_conn_rx","CONNECTION"),
                                "conn_isr_tx" : ("on_conn_tx","CONNECTION"),
            })
        if self.firmwareInformations["central"]:
            patchesList.update({
                                "ull_central_setup" : ("on_setup_central","CONNECTION"),
                                "ull_central_cleanup" : ("on_cleanup_central","CONNECTION"),
            })

        if self.firmwareInformations["peripheral"]:
            patchesList.update({
            "ull_peripheral_setup" : ("on_setup_peripheral","CONNECTION"),
            })
        for functionName,(targetName,dependency) in patchesList.items():
            instruction = self.findPatchableInstruction(functionName)
            if isinstance(instruction,list):
                address = thumb.extractInstructionAddress(instruction[0])
                instructionToReplace = thumb.extractTextFromInstruction(instruction[0])+";"+thumb.extractTextFromInstruction(instruction[1])
            else:
                address = thumb.extractInstructionAddress(instruction)
                instructionToReplace = thumb.extractTextFromInstruction(instruction)
            out += patch_generator.generateFunctionHookPatch(dependency, "rom", "hook_"+targetName, address, targetName, instructionToReplace)

        stackPointer = self.firmwareStructure["ram"][1]
        newStackPointer = self.firmwareStructure["ram_used"][1] - self.memoryZones["data_size"]
        out += patch_generator.generateValuePatch("COMMON", "rom", "hook_injected_stack_pointer",self.firmwareInformations["isr_vector"],newStackPointer)
        out += patch_generator.generateValuePatch("COMMON", "rom", "hook_injected_max_ram_address",self.datas["max_ram_address_pointer"],newStackPointer)

        return out


    def generateUsedFunctions(self):
        functions = {
            "memcpy":("void *","void * dst, void * src, uint32_t size"),
            "radio_is_done":("uint8_t",""),
            "radio_crc_is_valid":("bool",""),
            "ll_addr_get":("uint8_t *","uint8_t addr_type"),
         }
        if self.firmwareInformations["hci_support"]:
            functions.update({
                "bt_hci_evt_create":("void *","uint8_t opcode, size_t size"),
                "net_buf_simple_add":("void *","void * evt, size_t size"),
                "bt_recv":("void","void *evt")
            })

        self.firmwareInformations["used_functions"] = functions


    def generateLinkerScripts(self):
        functionsOut = ""
        self.generateUsedFunctions()

        functionsOut += linker_generator.generateFunctions({k:v for k,v in self.functions.items() if k in self.firmwareInformations["used_functions"].keys()})
        linkerOut = linker_generator.generateMemoryZonesAndSections()
        return (functionsOut,linkerOut)

    def generateWrapper(self):
        wrapperOut = ""
        wrapperOut += wrapper_generator.generateIncludes()+"\n"

        wrapperOut += wrapper_generator.generateComment("Constants and peripherals registers")
        wrapperOut += wrapper_generator.generateNrf52ZephyrWrapperHeader()

        wrapperOut += wrapper_generator.generateComment("Controller functions used by the wrapper")+"\n"
        for function,(returnValue,parameters) in self.firmwareInformations["used_functions"].items():
            wrapperOut += wrapper_generator.generateFunctionSignature(function,returnValue, parameters)+"\n"
        wrapperOut += "\n"

        wrapperOut += wrapper_generator.generateComment("Global variables used internally by the wrapper")
        wrapperOut += wrapper_generator.generateNrf52ZephyrWrapperGlobalsVariables(self.firmwareInformations["hci_support"])

        wrapperOut += wrapper_generator.generateComment("Generic Wrapper API")
        wrapperOut += wrapper_generator.generateNrf52ZephyrWrapperAPI()

        wrapperOut += wrapper_generator.generateComment("Actions API")
        wrapperOut += wrapper_generator.generateNrf52ZephyrWrapperActionsAPI(self.firmwareInformations["hci_support"])

        wrapperOut += wrapper_generator.generateComment("Hooks")
        wrapperOut += wrapper_generator.generateNrf52ZephyrWrapperHooks(self.firmwareInformations)

        return wrapperOut

    def generateConfiguration(self):
        configuration = ""
        stackPointer = self.firmwareStructure["ram_used"][1]
        if self.memoryZones["code_start"] is None or self.memoryZones["data_start"] is None:
            self.memoryZones["code_start"] = len(self.firmware) + self.memoryZones["data_size"]
            self.memoryZones["data_start"] = stackPointer - self.memoryZones["data_size"]
        capabilities = {i:self.firmwareInformations[i] for i in Controller.CAPABILITIES}
        configuration = conf_generator.generateConfiguration(self.name,capabilities,self.memoryZones["code_start"],self.memoryZones["code_size"], self.memoryZones["data_start"],self.memoryZones["data_size"],self.heapSize, self.firmwareStructure, self.interfaceType, architecture=self.firmwareInformations["architecture"], file_type=self.firmwareInformations["file_type"], gcc_flags=self.firmwareInformations["gcc_flags"])
        return configuration
