from oasis.controllers.analysis import thumb
from oasis.controllers.generators import target_generator

class Controller:
    CAPABILITIES = ["scanner","central","advertiser","peripheral","hci_support"]

    instructions = []
    firmware = b""
    firmwareStructure = {}
    firmwareInformations = {}
    functions = {}
    datas = {}

    def __init__(self,firmware):
        self.firmware = firmware
        self.name = None
        self.rootDirectory = None
        self.memoryZones = {}
        self.interfaceType = None
        self.instructions  = thumb.disassemble(firmware)

    def setParameters(self, name, interfaceType, codeSize,codeStart,dataSize,dataStart,heapSize, findMemoryZone):
        self.name = name
        self.interfaceType = interfaceType
        self.heapSize = heapSize
        self.memoryZones = {"code_start":codeStart,"code_size":codeSize,"data_start":dataStart, "data_size":dataSize, "strategy":findMemoryZone}

    def extractFirmwareStructure(self):
        pass

    def extractFirmwareInformations(self):
        pass
    def extractFunctions(self):
        pass

    def extractDatas(self):
        pass

    def showFunctions(self):
        for function,address in self.functions.items():
            if address is not None:
                print(function+" found at address "+hex(address))
            else:
                print(function+" not found !")

    def showDatas(self):
        for data,address in self.datas.items():
            if address is not None:
                print(data+" found at address "+hex(address))
            else:
                print(data+" not found !")

    def showCapabilities(self):
        for cap in self.CAPABILITIES:
            print(cap+" : "+("enabled" if cap in self.firmwareInformations and self.firmwareInformations[cap] else "disabled"))

    def generateCapabilities(self):
        pass

    def generatePatches(self):
        pass

    def generateWrapper(self):
        pass

    def generateLinkerScripts(self):
        pass

    def generateConfiguration(self):
        pass

    def generateTarget(self):
        patches = self.generatePatches()
        functionsLinkerScript, mainLinkerScript = self.generateLinkerScripts()
        wrapper = self.generateWrapper()
        configuration = self.generateConfiguration()
        if target_generator.generateTarget(self.firmwarePath, self.firmwareInformations["file_type"], self.name, configuration, wrapper, mainLinkerScript, functionsLinkerScript,patches):
            print("Target successfully generated !")
        else:
            print("An error occured during target generation.")
