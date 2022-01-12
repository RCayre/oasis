from .softdevice import SoftDeviceController
from .analysis import patterns,exceptions,disassembler
from .generators import patch_generator,linker_generator,conf_generator, wrapper_generator

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
            instructions = list(disassembler.exploreInstructions(self.instructions[i-512:i]))
            # find function prolog
            for instruction in instructions[::-1]:
                if "push" in instruction and "lr" in instruction: # prolog found
                    radioInterruptAddress = disassembler.extractInstructionAddress(instruction)
                    break
        if radioInterruptAddress is not None:
            return radioInterruptAddress
        else:
            raise exceptions.AddressNotFound


    def extractSetChannelMap(self):
        pattern = patterns.generatePattern([
            {"instruction":"ldrb r3,[r1,#4]"},
            {"instruction":"strb r3,[r0,#4]"},
            {"instruction":"bx lr"}

        ])

        setChannelMapAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            instructions = list(disassembler.exploreInstructions(self.instructions[i-16:i-14]))
            instruction = instructions[0]
            if "ldrb" in instruction and "r2, [r1, #0]" in instruction:
                setChannelMapAddress = disassembler.extractInstructionAddress(instruction)
                break
        if setChannelMapAddress is not None:
            return setChannelMapAddress
        else:
            raise exceptions.AddressNotFound

    def extractSetCrcInit(self):
        pattern = patterns.generatePattern([
            {"instruction":"lsls r0,r0,#8"},
    	    {"joker":2},
    	    {"instruction":"lsrs r0,r0,#8"},
    	    {"joker":2},
    	    {"instruction":"bx lr"},
        ])
        setCrcInitAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            setCrcInitAddress = i-24
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

        if setBdAddressAddress  is not None:
            return setBdAddressAddress
        else:
            raise exceptions.AddressNotFound


    def extractInitConnection(self):
        pattern = patterns.generatePattern([
            {"instruction":"adds r6,#0x60"},
            {"instruction":"adds r4,<X>","X":["#0x74","#0x78"]},
        ])
        initConnectionAddress = None

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
            instructions = list(disassembler.exploreInstructions(self.instructions[i:i+10]))
            if "bl" in instructions[-1]:
                target = disassembler.extractTargetAddressFromJump(instructions[-1])
                instructions2 = list(disassembler.exploreInstructions(self.instructions[target:target+6]))
                if "ldr" in instructions2[0] and "bx" in instructions2[-1] and "lr" in instructions2[-1]:
                    pointer = disassembler.extractTargetAddressFromLoadOrStore(instructions2[0])
                    gapRoleAddress = disassembler.extractValue(self.firmware[pointer:pointer+4])
                    break
        if gapRoleAddress is not None:
            return gapRoleAddress
        else:
            raise exceptions.AddressNotFound

    def extractInterruptType(self):
        if "radio_interrupt" not in self.functions:
            raise exceptions.AddressNotFound
        interruptTypeAddress = None
        instructions = list(disassembler.exploreInstructions(self.instructions[self.functions["radio_interrupt"]:self.functions["radio_interrupt"]+1024]))
        ldrbInstruction = None
        # find main ISR type
        for instruction in instructions:
            if "ldrb" in instruction:
                baseRegister = disassembler.extractBaseRegisterFromLoadOrStore(instruction)
                offset = disassembler.extractOffsetFromLoadOrStore(instruction)
                ldrbInstruction = instruction
                break
        if ldrbInstruction is not None:
            for instruction in instructions[:instructions.index(ldrbInstruction)][::-1]:
                if baseRegister+", [" in instruction and "ldr" in instruction:
                    pointer = disassembler.extractTargetAddressFromLoadOrStore(instruction)
                    interruptTypeAddress = disassembler.extractValue(self.firmware[pointer:pointer+4]) + offset
                    break
        interruptTypeCentralAddress = None
        # find central ISR type
        index = None
        candidates = []
        for instrIndex in range(len(instructions)-1):
            if "ldrb" in instructions[instrIndex] and "cmp" in instructions[instrIndex+1] and "#2" in instructions[instrIndex+1]:
                baseRegister = disassembler.extractBaseRegisterFromLoadOrStore(instructions[instrIndex])
                offset = disassembler.extractOffsetFromLoadOrStore(instructions[instrIndex])
                index = instrIndex

                for instruction in instructions[:index][::-1]:
                    if baseRegister+", [" in instruction and "ldr" in instruction:

                        pointer = disassembler.extractTargetAddressFromLoadOrStore(instruction)
                        candidates.append(disassembler.extractValue(self.firmware[pointer:pointer+4]) + offset)
                        break
        if len(candidates) > 0:
            interruptTypeCentralAddress = max([(candidates.count(i),i) for i in set(candidates)])[1]

        if interruptTypeAddress is not None and interruptTypeCentralAddress is not None:
            return (interruptTypeAddress,interruptTypeCentralAddress)
        else:
            raise exceptions.AddressNotFound

    def extractHopInterval(self):
        hopIntervalAddress = None
        pattern = patterns.generatePattern([
            {"instruction":"lsls r1,r1,#0x19"},
            {"instruction":"lsrs r1,r1,#0x1F"},


        ])
        for i in patterns.findPattern(self.firmware,pattern):
            instructions = list(disassembler.exploreInstructions(self.instructions[i:i+128]))

            for instruction in instructions:
                if "bl " in instruction and hex(self.functions["set_bd_address"])[2:] in instruction:
                    variableValue = None
                    blIndex = instructions.index(instruction)
                    baseRegister = disassembler.extractBaseRegisterFromLoadOrStore(instructions[blIndex-1])
                    offset = disassembler.extractOffsetFromLoadOrStore(instructions[blIndex-1])
                    sourceRegister = None
                    secondRegister = None
                    instructions2 = list(disassembler.exploreInstructions(self.instructions[i-512:i]))
                    for instruction2 in instructions2:
                        if "str" in instruction2 and "["+baseRegister+"," in instruction2 and "#"+str(offset) in instruction2:
                            loadingInstructions = instructions2[instructions2.index(instruction2)-5:instructions2.index(instruction2)+1]
                            sourceRegister = disassembler.extractDestRegisterFromLoadOrStore(loadingInstructions[-1])
                            break
                    if sourceRegister is not None:
                        for instruction2 in loadingInstructions:
                            if "adds" in instruction2 and disassembler.extractFirstRegisterFromAdds(instruction2) == sourceRegister:
                                secondRegister = disassembler.extractSecondRegisterFromAdds(instruction2)
                                offsetAdd = disassembler.extractOffsetFromAddOrSub(instruction2)
                                break
                        if secondRegister is not None:
                            for instruction2 in loadingInstructions:
                                if "ldr" in instruction2 and secondRegister in instruction2 and ";" in instruction2:
                                    pointer = disassembler.extractTargetAddressFromLoadOrStore(instruction2)
                                    value = disassembler.extractValue(self.firmware[pointer:pointer+4])
                                    variableValue = value+offsetAdd
                                    break

                    if variableValue is not None:
                        instructions3 = instructions[blIndex-1:blIndex+20]
                        for instrIndex in range(len(instructions3)-2):
                            if "lsls" in instructions3[instrIndex+2] and "ldrb" in instructions3[instrIndex]:
                                hopIntervalAddress = variableValue+disassembler.extractOffsetFromLoadOrStore(instructions3[instrIndex])
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
            instructions  = list(disassembler.exploreInstructions(self.instructions[i-64:i+4]))[::-1]
            if "bx" in instructions[0] and "lr" in instructions[0]:
                initSoftdeviceAddress = i
            else:
                for instrIndex in range(len(instructions)-1):
                    if ("push" in instructions[instrIndex]):
                        initSoftdeviceAddress = disassembler.extractInstructionAddress(instructions[instrIndex])
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

    def extractFunctions(self):
        try:
            self.functions["radio_interrupt"] = self.extractRadioInterrupt()
        except exceptions.AddressNotFound:
            print("Radio Interrupt: function not found !")

        try:
            self.functions["set_channel_map"] = self.extractSetChannelMap()
        except exceptions.AddressNotFound:
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
            self.functions["set_crc_init"] = self.extractSetCrcInit()
        except exceptions.AddressNotFound:
            print("Set Crc Init: function not found !")

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
            print("ISR Type: data not found !")

    def generatePatches(self):
        out = ""
        patchesList = {
            "init_softdevice" : ("on_init", "COMMON"),
            "radio_interrupt" : ("on_radio_interrupt","COMMON"),
            "set_bd_address" : ("on_set_bd_address","COMMON"),
            "init_connection" : ("on_init_connection","CONNECTION"),
            "set_access_address" : ("on_set_access_address","CONNECTION"),
            "set_crc_init" : ("on_set_crc_init","CONNECTION"),
            "set_channel_map" : ("on_set_channel_map","CONNECTION"),
        }
        for functionName,(targetName,dependency) in patchesList.items():
            references = [(i,disassembler.extractTextFromInstruction(self.instructions[i])) for i in disassembler.findReferences(self.instructions, self.functions[functionName])]
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

        configuration = conf_generator.generateConfiguration(self.name,self.memoryZones["code_start"],self.memoryZones["code_size"], self.memoryZones["data_start"],self.memoryZones["data_size"],self.heapSize, self.firmwareStructure, self.interfaceType, architecture=self.firmwareInformations["architecture"], file_type=self.firmwareInformations["file_type"], gcc_flags=self.firmwareInformations["gcc_flags"])
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
