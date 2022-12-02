from oasis.controllers.controller import Controller
from oasis.controllers.analysis import patterns,exceptions,esptools, reverse
import struct

class ESP32Controller(Controller):
    def __init__(self,filename):
        self.firmwarePath = filename
        self.header, firmware, self.segments, self.instructionPointer = esptools.imageToInternal(filename)
        Controller.__init__(self,firmware)

    def extractFirmwareStructure(self):
        for segment in self.segments:
            print(hex(segment["address"]), hex(segment["length"] + segment["address"]), segment["length"], segment["label"])
            print(segment["data"][:16].hex())

        func = esptools.readInImage(self.segments, 0x400836dc, 6*3)
        print(func.hex())
        #print(reverse.disasm(func, arch="xtensa", vma=0x400836dc))
        asmed = reverse.asm("""entry   a1, 32;
        extui   a12, a4, 0, 8;
        or      a11, a3, a3;
        or      a10, a2, a2;
        call8   0x4008d6a8;
        retw;
         """, arch="xtensa", vma=0x400836dc)
        print(asmed.hex())
        print(reverse.disasm(func, arch="xtensa", vma=0x400836dc))
        print(reverse.disasm(asmed, arch="xtensa", vma=0x400836dc))
        exit(1)

    def extractFirmwareInformations(self):
        exit(1)

    def extractDatas(self):
        exit(1)

    def generateCapabilities(self):
        exit(1)

    def findPatchableInstruction(self,function,size=32):
        exit(1)

    def generatePatches(self):
        exit(1)

    def generateUsedFunctions(self):
        exit(1)

    def generateLinkerScripts(self):
        exit(1)

    def generateWrapper(self):
        exit(1)

    def generateConfiguration(self):
        exit(1)
