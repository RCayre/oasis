from oasis.controllers.controller import Controller
from oasis.controllers.analysis import hextools,patterns,thumb,exceptions
import struct

class SoftDeviceController(Controller):
    startOffset = None
    codeSegment = None
    instructionPointer = None

    def __init__(self,filename):
        self.firmwarePath = filename
        self.startOffset,firmware,self.codeSegment,self.instructionPointer = hextools.hexToInternal(filename)
        Controller.__init__(self,firmware)

    def extractFirmwareStructure(self):
        for i in  range(0x1000,len(self.firmware)-4*21,0x100):
            stackPointer = struct.unpack('I',self.firmware[i:i+4])[0]
            callbacks = struct.unpack('I'*20,self.firmware[i+4:i+4+4*20])
            if stackPointer >= 0x20002000 and stackPointer <= 0x30000000 and all([c == 0 or c <= 0x20000000 for c in callbacks]):
                self.firmwareStructure["softdevice_rom"] = (self.startOffset,i-1)
                self.firmwareStructure["application_rom"] = (i,len(self.firmware)-self.startOffset)
                self.firmwareStructure["rom"] = (self.startOffset,len(self.firmware)-self.startOffset)
                self.firmwareStructure["ram"] = (0x20000000,stackPointer)
                self.firmwareInformations["isr_vector"] = i
        print(self.firmwareStructure)


    def extractSetChannel(self):
        pattern = patterns.generatePattern([
            {"instruction":"cmp r0,#0x25"},
        ])
        setChannelAddress = None
        secondInstructionFound = False
        thirdInstructionFound = False
        for i in patterns.findPattern(self.firmware,pattern):
            instructions = list(thumb.exploreInstructions(self.instructions[i:i+32]))
            for instruction in instructions:
                if "cmp" in instruction and "#38" in instruction and "r0," in instruction:
                    secondInstructionFound = True
                if "cmp" in instruction and "#39" in instruction and "r0," in instruction:
                    thirdInstructionFound = True
                if secondInstructionFound and thirdInstructionFound:
                    setChannelAddress = i
                    break
            if setChannelAddress is not None:
                break
        if setChannelAddress is not None:
            return setChannelAddress
        else:
            raise exceptions.AddressNotFound


    def extractSetAccessAddress(self):
        pattern = patterns.generatePattern([
            {"instruction":"lsls <X>,<X>,#8","X":["r0","r3"]},
            {"instruction":"<X>","X":["adds r1,#12","str r0,[r1,#0]","orrs r0,r3"]}
        ])
        setAccessAddressAddress = None

        for i in patterns.findPattern(self.firmware,pattern):
            instructions = list(thumb.exploreInstructions(self.instructions[i-16:i]))[::-1]
            if "ldrb" in "\n".join(instructions):
                for j in range(len(instructions)):
                    if "bx" in instructions[j] and "lr" in instructions[j]:
                        setAccessAddressAddress  = thumb.extractInstructionAddress(instructions[j-1])

                        break

        if setAccessAddressAddress  is not None:
            return setAccessAddressAddress
        else:
            raise exceptions.AddressNotFound
