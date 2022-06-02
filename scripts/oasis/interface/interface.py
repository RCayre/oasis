from oasis.utils import conf_parser

class Interface:

    def __init__(self,target):
        ram_start,ram_end = conf_parser.getTargetRam(target)
        rom_start,rom_end = conf_parser.getTargetRom(target)
        self.memoryZones = {"rom":(rom_start,rom_end), "ram":(ram_start,ram_end)}
        self.interface = conf_parser.getTargetInterface(target)
        self.target = target
        self.firmwarePath = conf_parser.getTargetFirmwareFile(target)
        (code_start, code_size),(data_start, data_size) = conf_parser.getTargetCodeZone(target), conf_parser.getTargetDataZone(target)
        self.codeZone = {"code_start":code_start, "code_size":code_size}
        self.dataZone = {"data_start":data_start, "data_size":data_size}
        self.connected = False
        self.patchingSuccessful = False

    def isPatchingSuccessful(self):
        return self.patchingSuccessful

    def checkSupport(self,feature):
        return False

    def connect(self):
        pass

    def disconnect(self):
        pass

    def sendHciCommand(self,opcode,data):
        pass

    def writeRam(self, address, value):
        pass

    def writeRom(self, address, value):
        pass

    def log(self):
        pass

    def write(self, address, value):
        pass

    def patchRam(self, address, value):
        pass

    def patchRom(self, address, value):
        pass

    def patch(self, address, value):
        pass

    def read(self,address,length):
        pass
