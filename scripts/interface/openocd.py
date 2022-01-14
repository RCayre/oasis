from interface.interface import Interface
from controllers.analysis import hextools
from utils import conf_parser,patch_parser,builder,exec
import subprocess

class OpenocdInterface(Interface):

    def instantiateOpenocd(self):
        if self.interface == "NRF51_JLINK_OPENOCD":
            self.debugger = "jlink"
            self.chip = "nrf51"
        elif self.interface == "NRF51_STLINK_OPENOCD":
            self.debugger = "stlink"
            self.chip = "nrf51"

    def sendHciCommand(self,opcode,data):
        print("Current target does not support HCI.")

    def openFirmwareHexFile(self):
        firmwareFile = conf_parser.getTargetFirmwareFile(self.target)
        self.startOffset, self.content , self.codeSegment, self.instructionPointer = hextools.hexToInternal(firmwareFile)
        self.initialLength = len(self.content)

    def __init__(self, target):
        Interface.__init__(self, target)
        self.instantiateOpenocd()
        self.patching = False

    def applyPatches(self):
        # Generate hex patched file
        content = hextools.internalToHex(self.startOffset, self.content, self.codeSegment, self.instructionPointer, self.initialLength)
        builder.buildPatchedHexFirmware(content)

        # program target
        #print(" ".join(["openocd","-f","interface/"+self.debugger+".cfg"]+(["-c","transport select swd","-c","set WORKAREASIZE 0"] if self.debugger == "jlink" else [])+["-f","target/"+self.chip+".cfg","-c","init","-c", "reset init", "-c","halt", "-c" ,"nrf51 mass_erase", "-c" ,"program "+builder.getPatchedHexFirmware()+" verify", "-c","reset","-c","exit"]))
        out,err = exec.execute_with_output(["openocd","-f","interface/"+self.debugger+".cfg"]+(["-c","transport select swd","-c","set WORKAREASIZE 0"] if self.debugger == "jlink" else [])+["-f","target/"+self.chip+".cfg","-c","init","-c", "reset init", "-c","halt", "-c" ,"nrf51 mass_erase", "-c" ,"program "+builder.getPatchedHexFirmware()+" verify", "-c","reset","-c","exit"])
        if b"Verified OK" in err:
            print("Patching successful.")
        else:
            print("Failure during patching.")

    def connect(self):
        if exec.check_execution(["openocd","-f","interface/"+self.debugger+".cfg"]+(["-c","transport select swd"] if self.debugger == "jlink" else []) + ["-f","target/"+self.chip+".cfg","-c","init","-c","exit"]):
            print("Interface connected !")
            self.connected = True
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
                    if newLog != logContent and logContent[0] != 0:
                        newLog = logContent
                        yield newLog[1:1+newLog[0]]

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
