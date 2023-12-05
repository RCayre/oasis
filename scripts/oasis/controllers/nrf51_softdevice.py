from oasis.controllers.softdevice import SoftDeviceController, Controller
from oasis.controllers.analysis import patterns,exceptions,thumb
from oasis.controllers.generators import patch_generator,linker_generator,conf_generator, wrapper_generator
from struct import unpack
class NRF51SoftDeviceController(SoftDeviceController):

    def extractFirmwareInformations(self):
        self.firmwareInformations["architecture"] = "armv6s-m"
        self.firmwareInformations["gcc_flags"] = "-DALIGNED_MALLOC -lgcc -static-libgcc -mno-unaligned-access"
        self.firmwareInformations["file_type"] = "hex"

    def extractRadioInterrupt(self):
        pattern = patterns.generatePattern([
            {"value":"40150040"}, # Radio register
        ])
        radioInterruptAddress = None

        # find function by identifying radio register
        for i in patterns.findPattern(self.firmware,pattern):
            instructions = list(thumb.exploreInstructions(self.instructions[i-512:i]))
            # find function prolog
            for instruction in instructions[::-1]:
                if "push" in instruction and "lr" in instruction: # prolog found
                    radioInterruptAddress = thumb.extractInstructionAddress(instruction)
                    break
        if radioInterruptAddress is not None:
            return radioInterruptAddress
        else:
            raise exceptions.AddressNotFound


    def extractSetChannelMap(self):

        pattern = patterns.generatePattern([
            {"instruction":"ldrb <X>,[r1,#4]", "X":["r3"]},
            {"instruction":"strb <X>,[r0,#4]", "X":["r3"]},
            {"instruction":"bx lr"}

        ])

        setChannelMapAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            instructions = list(thumb.exploreInstructions(self.instructions[i-16:i-14]))
            instruction = instructions[0]
            if "ldrb" in instruction and "r2, [r1, #0]" in instruction:
                setChannelMapAddress = thumb.extractInstructionAddress(instruction)
                break
        if setChannelMapAddress is not None:
            return setChannelMapAddress
        else:
            raise exceptions.AddressNotFound

    def extractSetCrcInit(self):
        pattern1 = patterns.generatePattern([
            {"instruction":"lsls r0,r0,#8"},
    	    {"joker":2},
    	    {"instruction":"lsrs r0,r0,#8"},
    	    {"joker":2},
    	    {"instruction":"<X>", "X":["bx lr", "pop {r4, pc}"]},
        ])
        setCrcInitAddress = None

        for i in patterns.findPattern(self.firmware,pattern1):
            setCrcInitAddress = (i-24) if "pop" not in self.instructions[i+8] else (i-6)
            break

        if setCrcInitAddress  is not None:
            return setCrcInitAddress
        else:
            raise exceptions.AddressNotFound

    def extractSetBdAddress(self):
        pattern = patterns.generatePattern([
            {"instruction":"ldrb r2,[r1,#0x5]"},
    	    {"instruction":"strb r2,[r0,#0x5]"},
    	    {"instruction":"bx lr"},
        ])
        setBdAddressAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            setBdAddressAddress = i-20
            break

        # Method 2
        if setBdAddressAddress is None and "memcpy" in self.functions:
            candidates = []
            for reference in thumb.findReferences(self.instructions, self.functions["memcpy"]):
                instructions = list(thumb.exploreInstructions(self.instructions[reference-12:reference]))
                for instrIndex in range(1, len(instructions)-1):#print(self.instructions[reference-4:reference])
                    if (
                        "push" in instructions[instrIndex-1] and
                        "mov" in instructions[instrIndex] and "r2" in instructions[instrIndex] and "#6" in instructions[instrIndex] and
                        "adds" in instructions[instrIndex+1] and "r0" in instructions[instrIndex+1] and "#3" in instructions[instrIndex+1]
                        ):
                        setBdAddressAddress =  thumb.extractInstructionAddress(instructions[instrIndex-1])
        if setBdAddressAddress  is not None:
            return setBdAddressAddress
        else:
            raise exceptions.AddressNotFound


    def extractInitConnection(self):
        initConnectionAddress = None
        if "memcpy" in self.functions:
            pattern = patterns.generatePattern([
                {"instruction":"push {r3-r7, lr}"},
                {"joker":4},
                {"instruction":"cmp r1, #1"}
            ])
            candidates = []
            for reference in thumb.findReferences(self.instructions, self.functions["memcpy"]):
                for i in patterns.findPattern(self.firmware[reference-512:reference], pattern):
                    initConnectionAddress = i+reference-512
                    break
        else:
            pattern = patterns.generatePattern([
            {"instruction":"adds r6,#0x60"},
            {"instruction":"adds r4,<X>","X":["#0x74","#0x78"]},
            ])

            for i in patterns.findPattern(self.firmware,pattern):
                initConnectionAddress = i-8
                break

        if initConnectionAddress  is not None:
            return initConnectionAddress
        else:
            raise exceptions.AddressNotFound

    def extractGapRole(self):
        pattern = patterns.generatePattern([
            {"instruction":"strb r6,[r4,#0x12]"},
            {"instruction":"strb r6,[r4,#0x13]"},
            {"instruction":"strb r6,[r5,#1]"},

        ])
        gapRoleAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            instructions = list(thumb.exploreInstructions(self.instructions[i:i+10]))
            if "bl" in instructions[-1]:
                target = thumb.extractTargetAddressFromJump(instructions[-1])
                instructions2 = list(thumb.exploreInstructions(self.instructions[target:target+6]))
                if "ldr" in instructions2[0] and "bx" in instructions2[-1] and "lr" in instructions2[-1]:
                    pointer = thumb.extractTargetAddressFromLoadOrStore(instructions2[0])
                    gapRoleAddress = thumb.extractValue(self.firmware[pointer:pointer+4])
                    break
        if gapRoleAddress is not None:
            return gapRoleAddress
        else:
            raise exceptions.AddressNotFound

    def extractInterruptType(self):
        if "radio_interrupt" not in self.functions:
            raise exceptions.AddressNotFound

        interruptTypeAddress = None
        instructions = list(thumb.exploreInstructions(self.instructions[self.functions["radio_interrupt"]:self.functions["radio_interrupt"]+1024]))
        ldrbInstruction = None
        # find main ISR type
        for instruction in instructions:
            if "ldrb" in instruction:
                baseRegister = thumb.extractBaseRegisterFromLoadOrStore(instruction)
                offset = thumb.extractOffsetFromLoadOrStore(instruction)
                ldrbInstruction = instruction
                break
        if ldrbInstruction is not None:

            for instruction in instructions[:instructions.index(ldrbInstruction)][::-1]:
                if baseRegister+", [" in instruction and "ldr" in instruction:
                    pointer = thumb.extractTargetAddressFromLoadOrStore(instruction)
                    interruptTypeAddress = thumb.extractValue(self.firmware[pointer:pointer+4]) + offset
                    break
        interruptTypeCentralAddress = None
        # find central ISR type
        index = None
        candidates = []
        for instrIndex in range(len(instructions)-1):
            if "ldrb" in instructions[instrIndex] and "cmp" in instructions[instrIndex+1] and "#2" in instructions[instrIndex+1]:
                baseRegister = thumb.extractBaseRegisterFromLoadOrStore(instructions[instrIndex])
                offset = thumb.extractOffsetFromLoadOrStore(instructions[instrIndex])
                index = instrIndex

                for instruction in instructions[:index][::-1]:
                    if baseRegister+", [" in instruction and "ldr" in instruction:

                        pointer = thumb.extractTargetAddressFromLoadOrStore(instruction)
                        candidates.append(thumb.extractValue(self.firmware[pointer:pointer+4]) + offset)
                        break
        if len(candidates) > 0:
            interruptTypeCentralAddress = max([(candidates.count(i),i) for i in set(candidates)])[1]

        if interruptTypeAddress is not None and interruptTypeCentralAddress is not None:
            return (interruptTypeAddress,interruptTypeCentralAddress)
        elif interruptTypeAddress is not None:
            return (interruptTypeAddress,None)
        else:
            raise exceptions.AddressNotFound

    def extractHopInterval(self):
        hopIntervalAddress = None
        pattern = patterns.generatePattern([
            {"instruction":"lsls r1,r1,#0x19"},
            {"instruction":"lsrs r1,r1,#0x1F"},


        ])
        for i in patterns.findPattern(self.firmware,pattern):
            instructions = list(thumb.exploreInstructions(self.instructions[i:i+128]))

            for instruction in instructions:
                if "bl " in instruction and hex(self.functions["set_bd_address"])[2:] in instruction:
                    variableValue = None
                    blIndex = instructions.index(instruction)
                    baseRegister = thumb.extractBaseRegisterFromLoadOrStore(instructions[blIndex-1])
                    offset = thumb.extractOffsetFromLoadOrStore(instructions[blIndex-1])
                    sourceRegister = None
                    secondRegister = None
                    instructions2 = list(thumb.exploreInstructions(self.instructions[i-512:i]))
                    for instruction2 in instructions2:

                        if "str" in instruction2 and "["+baseRegister+"," in instruction2 and "#"+str(offset) in instruction2:
                            loadingInstructions = instructions2[instructions2.index(instruction2)-5:instructions2.index(instruction2)+1]
                            sourceRegister = thumb.extractDestRegisterFromLoadOrStore(loadingInstructions[-1])
                            break
                    if sourceRegister is not None:
                        for instruction2 in loadingInstructions:
                            if "adds" in instruction2 and thumb.extractFirstRegisterFromAdds(instruction2) == sourceRegister:
                                secondRegister = thumb.extractSecondRegisterFromAdds(instruction2)
                                offsetAdd = thumb.extractOffsetFromAddOrSub(instruction2)
                                break
                        if secondRegister is not None:
                            for instruction2 in loadingInstructions:
                                if "ldr" in instruction2 and secondRegister in instruction2 and (";" in instruction2 or "@" in instruction2):
                                    pointer = thumb.extractTargetAddressFromLoadOrStore(instruction2)
                                    value = thumb.extractValue(self.firmware[pointer:pointer+4])
                                    variableValue = value+offsetAdd
                                    break

                    if variableValue is not None:
                        instructions3 = instructions[blIndex-1:blIndex+20]
                        for instrIndex in range(len(instructions3)-2):
                            if "lsls" in instructions3[instrIndex+2] and "ldrb" in instructions3[instrIndex]:
                                hopIntervalAddress = variableValue+thumb.extractOffsetFromLoadOrStore(instructions3[instrIndex])
                                break
        if hopIntervalAddress is not None:
            return hopIntervalAddress
        else:
            raise exceptions.AddressNotFound

    def extractInitSoftdevice(self):
        pattern = patterns.generatePattern([
        {"instruction":"svc 0x10"}
        ])
        initSoftdeviceAddress = None

        for i in patterns.findPattern(self.firmware, pattern):
            instructions  = list(thumb.exploreInstructions(self.instructions[i-64:i+4]))[::-1]
            if "bx" in instructions[0] and "lr" in instructions[0]:
                initSoftdeviceAddress = i
            else:
                for instrIndex in range(len(instructions)-1):
                    if ("push" in instructions[instrIndex]):
                        initSoftdeviceAddress = thumb.extractInstructionAddress(instructions[instrIndex])
                        break
        if initSoftdeviceAddress is not None:
            return initSoftdeviceAddress
        else:
            raise exceptions.AddressNotFound

    def extractWaitSoftdevice(self):
        pattern = patterns.generatePattern([
        {"instruction":"svc 0x48"}
        ])
        waitSoftdeviceAddress = None

        for i in patterns.findPattern(self.firmware, pattern):
            waitSoftdeviceAddress = i
            break
        if waitSoftdeviceAddress is not None:
            return waitSoftdeviceAddress
        else:
            raise exceptions.AddressNotFound

    def extractMemcpy(self):
        pattern = patterns.generatePattern([
        {"instruction":"push {r3-r7, lr}"},
        {"instruction":"cmp r2, #4"},
        {"joker":2},
        {"instruction":"lsls r3, r0, #0x1e"},
        ])
        memcpyAddress = None

        for i in patterns.findPattern(self.firmware, pattern):
            memcpyAddress = i
            break
        if memcpyAddress is not None:
            return memcpyAddress
        else:
            raise exceptions.AddressNotFound

    def extractChannelMap(self):
        if "init_connection" not in self.functions:
            raise exceptions.AddressNotFound
        instructions = list(thumb.exploreInstructions(self.instructions[self.functions["init_connection"]:self.functions["init_connection"] + 512]))

        addsOffset = None
        loadOffset = None
        pointerAddress = None
        connectionStructureAddress = None
        for instrIndex in range(len(instructions)-4):
            if (
                "mov" in instructions[instrIndex] and
                "r2" in instructions[instrIndex] and
                "#5" in instructions[instrIndex] and
                "adds" in instructions[instrIndex+2] and
                "r0" in instructions[instrIndex+2]
            ):
                addsOffset = thumb.extractOffsetFromAddOrSub(instructions[instrIndex+2])

                for instruction in list(instructions[instrIndex-80:instrIndex])[::-1]:
                    if "ldr" in instruction and "r0" in instruction and "r4" in instruction:
                        loadOffset = int(instruction.split(" ")[-1].split("]")[0].replace("#", ""))
                    if "pc" in instruction:
                        pointerAddress = thumb.extractTargetAddressFromLoadOrStore(instruction)
                    if addsOffset is not None and loadOffset is not None and pointerAddress is not None:
                        connectionStructureAddress = unpack("I", self.firmware[pointerAddress:pointerAddress+4])[0]  + loadOffset
                        break
                if connectionStructureAddress is not None:
                    break
        if connectionStructureAddress is not None and addsOffset is not None:
            return connectionStructureAddress, addsOffset
        else:
            raise exceptions.AddressNotFound

    def extractFunctions(self):
        try:
            self.functions["radio_interrupt"] = self.extractRadioInterrupt()
        except exceptions.AddressNotFound:
            print("Radio Interrupt: function not found !")

        try:
            self.functions["set_crc_init"] = self.extractSetCrcInit()
        except exceptions.AddressNotFound:
            print("Set Crc Init: function not found !")

        try:
            self.functions["set_channel_map"] = self.extractSetChannelMap()
        except exceptions.AddressNotFound:
            try:
                self.functions["memcpy"] = self.extractMemcpy()
            except exceptions.AddressNotFound:
                print("Memcpy not found !")
                print("Set Channel Map: function not found !")

        try:
            self.functions["set_channel"] = self.extractSetChannel()
        except exceptions.AddressNotFound:
            print("Set Channel: function not found !")

        try:
            self.functions["set_access_address"] = self.extractSetAccessAddress()
        except exceptions.AddressNotFound:
            print("Set Access Address: function not found !")

        try:
            self.functions["set_bd_address"] = self.extractSetBdAddress()
        except exceptions.AddressNotFound:
            print("Set Bd Address: function not found !")

        try:
            self.functions["init_connection"] = self.extractInitConnection()
        except exceptions.AddressNotFound:
            print("Init Connection: function not found !")

        try:
            self.functions["init_softdevice"] =  self.extractInitSoftdevice()
        except exceptions.AddressNotFound:
            print("Init SoftDevice: function not found !")
        try:
            self.functions["wait_softdevice"] = self.extractWaitSoftdevice()
        except exceptions.AddressNotFound:
            print("Wait SoftDevice: function not found !")

    def extractDatas(self):
        try:
            self.datas["gap_role"] = self.extractGapRole()
        except exceptions.AddressNotFound:
            print("Gap role: data not found !")

        try:
            self.datas["interrupt_type"],self.datas["interrupt_type_central"] = self.extractInterruptType()
        except exceptions.AddressNotFound:
            print("ISR Type: data not found !")

        try:
            self.datas["hop_interval"] = self.extractHopInterval()
        except exceptions.AddressNotFound:
            print("Hop interval: data not found !")
        except:
            print("Hop interval: data not found !")

        if "set_channel_map" not in self.functions and "init_connection" in self.functions:
            try:
                self.datas["connection_structure"], self.datas["channel_map_offset"] = self.extractChannelMap()
            except exceptions.AddressNotFound:
                print("Channel Map: function not found !")

    def generateCapabilities(self):
        self.firmwareInformations["scanner"] = True
        self.firmwareInformations["peripheral"] = True
        self.firmwareInformations["central"] = True
        self.firmwareInformations["advertiser"] = True
        self.firmwareInformations["hci_support"] = False

    def generatePatches(self):
        out = ""
        patchesList = {
            "init_softdevice" : ("on_init", "COMMON"),
            "radio_interrupt" : ("on_radio_interrupt","COMMON"),
            "set_bd_address" : ("on_set_bd_address","COMMON"),
            "wait_softdevice" : ("on_event_loop","COMMON"),
            "init_connection" : ("on_init_connection","CONNECTION"),
            "set_access_address" : ("on_set_access_address","CONNECTION"),
            "set_crc_init" : ("on_set_crc_init","CONNECTION"),
            "set_channel_map" : ("on_set_channel_map","CONNECTION"),
        }
        for functionName,(targetName,dependency) in patchesList.items():
            references = [(i,thumb.extractTextFromInstruction(self.instructions[i])) for i in thumb.findReferences(self.instructions, self.functions[functionName])]
            for referenceIndex in range(len(references)):
                address, instructionToReplace = references[referenceIndex]
                targetNameNumbered = targetName+str(referenceIndex)
                out += patch_generator.generateFunctionHookPatch(dependency, "rom", "hook_"+targetNameNumbered, address, targetName, instructionToReplace)
        out += patch_generator.generateFunctionPointerPatch("COMMON", "rom", "hook_on_timer_interrupt",self.firmwareInformations["isr_vector"] + 0x68,"on_timer_interrupt")
        stackPointer = self.firmwareStructure["ram"][1]
        pattern = patterns.generateValuePattern(stackPointer)
        applicationBaseAddress = self.firmwareStructure["application_rom"][0]
        newStackPointer = stackPointer - self.memoryZones["data_size"]
        count = 1
        for i in patterns.findPattern(self.firmware[applicationBaseAddress:],pattern):
            out += patch_generator.generateValuePatch("COMMON", "rom", "hook_injected_stack_pointer"+str(count),applicationBaseAddress+i,newStackPointer)
            count += 1
        return out

    def generateLinkerScripts(self):
        functionsOut = "" # no need to direct call an internal function in this implementation
        linkerOut = linker_generator.generateMemoryZonesAndSections()
        return functionsOut,linkerOut

    def generateConfiguration(self):
        configuration = ""
        stackPointer = self.firmwareStructure["ram"][1]
        if self.memoryZones["code_start"] is None or self.memoryZones["data_start"] is None:
            self.memoryZones["code_start"] = len(self.firmware) + self.memoryZones["data_size"]
            self.memoryZones["data_start"] = stackPointer - self.memoryZones["data_size"]

        capabilities = {i:self.firmwareInformations[i] for i in Controller.CAPABILITIES}
        configuration = conf_generator.generateConfiguration(self.name,capabilities,self.memoryZones["code_start"],self.memoryZones["code_size"], self.memoryZones["data_start"],self.memoryZones["data_size"],self.heapSize, self.firmwareStructure, self.interfaceType, architecture=self.firmwareInformations["architecture"], file_type=self.firmwareInformations["file_type"], gcc_flags=self.firmwareInformations["gcc_flags"])
        return configuration

    def generateWrapper(self):
        wrapperOut = ""
        wrapperOut += wrapper_generator.generateIncludes()+"\n"

        wrapperOut += wrapper_generator.generateComment("Constants and peripherals registers")
        wrapperOut += wrapper_generator.generateNrf51SoftdeviceWrapperHeader()

        wrapperOut += wrapper_generator.generateComment("Global variables used internally by the wrapper")
        wrapperOut += wrapper_generator.generateNrf51SoftdeviceWrapperGlobalsVariables(self.datas)

        wrapperOut += wrapper_generator.generateComment("Generic Wrapper API")
        wrapperOut += wrapper_generator.generateNrf51SoftdeviceWrapperAPI()

        wrapperOut += wrapper_generator.generateComment("Actions API")
        wrapperOut += wrapper_generator.generateNrf51SoftdeviceWrapperActionsAPI()

        wrapperOut += wrapper_generator.generateComment("Hooks")
        wrapperOut += wrapper_generator.generateNrf51SoftdeviceWrapperHooks()

        return wrapperOut
