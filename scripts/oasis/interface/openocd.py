from oasis.interface.interface import Interface
from oasis.controllers.analysis import hextools
from oasis.utils import conf_parser,patch_parser,builder,exec,hci
import subprocess,struct

class OpenocdInterface(Interface):

    def instantiateOpenocd(self):
        if self.interface == "NRF51_JLINK_OPENOCD":
            self.debugger = "jlink"
            self.chip = "nrf51"
        elif self.interface == "NRF51_STLINK_OPENOCD":
            self.debugger = "stlink"
            self.chip = "nrf51"
        elif self.interface == "NRF52_STLINK_OPENOCD":
            self.debugger = "stlink"
            self.chip = "nrf52"
        elif self.interface == "NRF52_JLINK_OPENOCD":
            self.debugger = "jlink"
            self.chip = "nrf52"

    def instantiateHci(self):
        compatibleInterfaces = hci.listCompatibleHciInterfaces()
        if len(compatibleInterfaces) > 0:
            self.hciSocket = hci.HCISocket(compatibleInterfaces[0])
        else:
            self.hciSocket = None

    def sendHciCommand(self,opcode,data):
        print("Current target does not support HCI.")

    def openFirmwareHexFile(self):
        firmwareFile = conf_parser.getTargetFirmwareFile(self.target)
        self.startOffset, self.content , self.codeSegment, self.instructionPointer = hextools.hexToInternal(firmwareFile)
        self.initialLength = len(self.content)

    def __init__(self, target):
        Interface.__init__(self, target)
        self.capabilities = conf_parser.getTargetCapabilities(target)
        self.instantiateOpenocd()
        self.hciSocket = None
        self.patching = False

    def applyPatches(self):
        # Generate hex patched file
        content = hextools.internalToHex(self.startOffset, self.content, self.codeSegment, self.instructionPointer, self.initialLength)
        builder.buildPatchedHexFirmware(content)
        out,err = exec.execute_with_output(["openocd","-f","interface/"+self.debugger+".cfg"]+(["-c","transport select swd","-c","set WORKAREASIZE 0"] if self.debugger == "jlink" else [])+["-f","target/"+self.chip+".cfg","-c","init","-c", "reset init", "-c","halt", "-c","nrf5 mass_erase","-c" ,"program "+builder.getPatchedHexFirmware()+" verify", "-c","reset","-c","exit"])
        if b"Verified OK" in err:
            self.patchingSuccessful = True
        else:
            self.patchingSuccessful = False

    def checkOpenOCDDebugger(self):
        return exec.check_execution(["openocd","-f","interface/"+self.debugger+".cfg"]+(["-c","transport select swd"] if self.debugger == "jlink" else []) + ["-f","target/"+self.chip+".cfg","-c","init","-c","exit"])

    def checkSupport(self,feature):
        if feature == "LOG":
            return ("hci_support" in self.capabilities and len(hci.listCompatibleHciInterfaces()) > 0) or ("hci_support" not in self.capabilities and self.checkOpenOCDDebugger())
        elif feature == "PATCH" or feature == "READ" or feature == "WRITE":
            return self.checkOpenOCDDebugger()
        else:
            return False

    def connect(self):
        if self.checkOpenOCDDebugger():
            self.connected = True
        if self.checkSupport("LOG") and "hci_support" in self.capabilities:
            self.instantiateHci()
            self.connected = True

        if self.connected:
            print("Interface connected !")
        else:
            print("Interface error: not connection to the target device.")
            exit(1)

    def disconnect(self):
        # here we have to apply the patches and flash our modified firmware
        if self.connected:
            if self.patching:
                self.applyPatches()
            self.connected = False

    def writeRam(self, address, value):
        pass

    def writeRom(self, address, value):
        pass

    def write(self, address, value):
        if self.memoryZones["rom"][0] >= address and address <= self.memoryZones["rom"][1]:
            return self.writeRom(address,value)
        else:
            return self.writeRam(address,value)

    def log(self):
        if self.hciSocket is not None:
            while True:
                packet = self.hciSocket.recv()
                if len(packet) > 3 and packet[1] == 0xFF:
                    yield packet[3:]
        else:
            patches = patch_parser.getMapping(self.target)
            if patches is None:
                return None
            else:
                logAddress = None
                logMaxSize = None
                for patch in patches:
                    if patch["patch_name"] == "log_buffer":
                        logAddress = patch["patch_address"]
                        logMaxSize = len(patch["patch_content"])
                        break
                if logAddress is not None:
                    newLog = None
                    while True:
                        logContent = self.read(logAddress,logMaxSize)
                        if newLog is None:
                            newLog = logContent
                            pass
                        if newLog[0] != logContent[0] and logContent[1] != 0:
                            newLog = logContent
                            yield newLog[2:2+newLog[1]]

    def patchRam(self, address, value):
        if not self.patching:
            self.patching = True
            self.openFirmwareHexFile()

        addressInHex = address - self.dataZone["data_start"] + (self.codeZone["code_start"] - self.dataZone["data_size"])
        if addressInHex + len(value) >= self.codeZone["code_start"]:
            return False
        else:
            try:
                self.content = hextools.writeInHex(self.content, self.startOffset, addressInHex, value)
                return True
            except:
                return False

    def patchRom(self, address, value):
        if not self.patching:
            self.patching = True
            self.openFirmwareHexFile()

        try:
            self.content = hextools.writeInHex(self.content, self.startOffset, address, value)
            return True
        except:
            return False

    def patch(self, address, value):
        if not self.patching:
            self.patching = True
            self.openFirmwareHexFile()

        if address >= self.dataZone["data_start"]:
            return self.patchRam(address, value)
        else:
            return self.patchRom(address, value)

    def read(self,address,length):
        content = None
        for output in exec.execute(["openocd","-f","interface/"+self.debugger+".cfg"]+(["-c","transport select swd"] if self.debugger == "jlink" else []) +["-f","target/"+self.chip+".cfg", "-c", "init", "-c "+self.chip+".cpu mdb "+"0x{:08x}".format(address)+" "+"{:d}".format(length), "-c exit"]):
            if "0x{:08x}".format(address) in output:
                content = ""
            if content is not None and ":" in output:
                content += output.split(":")[1].replace("\n","").replace(" ","")
        return bytes.fromhex(content)
