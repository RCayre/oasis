from oasis.interface.interface import Interface
from oasis.controllers.analysis import hextools
from oasis.utils import conf_parser,patch_parser,builder,exec,hci
import subprocess,struct,os

class NRFUtilInterface(Interface):
    def instantiateNrfutil(self):
        if self.interface == "NRF52_NRFUTIL":
            self.serial = self.autoFindSerialPort()
            self.chip = "nrf52"

    def autoFindSerialPort(self):
        if os.path.isdir("/dev/serial") and os.path.isdir("/dev/serial/by-id"):
            allowedDevices = [os.readlink("/dev/serial/by-id/"+i).replace("../../", "/dev/") for i in os.listdir("/dev/serial/by-id") if "Nordic_Semiconductor_Open_DFU_Bootloader" in i]
            if len(allowedDevices) > 0:
                return allowedDevices[0]
            else:
                return None
        else:
            return None

    def checkSerialPort(self):
        return self.autoFindSerialPort() is not None

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
        self.hciSocket = None
        self.patching = False

    def checkSupport(self,feature):
        if feature == "LOG":
            return "hci_support" in conf_parser.getTargetCapabilities(self.target) and len(hci.listCompatibleHciInterfaces()) > 0
        elif feature == "PATCH":
            return self.checkSerialPort()
        else:
            return False

    def applyPatches(self):
        # Generate hex patched file
        content = hextools.internalToHex(self.startOffset, self.content, self.codeSegment, self.instructionPointer, self.initialLength)
        builder.buildPatchedHexFirmware(content)
        out,err = exec.execute_with_output(["nrfutil","pkg","generate", "--hw-version" ,("52" if self.chip == "nrf52" else "51"), "--sd-req","0x00", "--debug-mode","--application",builder.getPatchedHexFirmware(),"build/dfu.zip"])
        if b"Zip created at" in out:
            out,err = exec.execute_with_output(["nrfutil","dfu","usb-serial","-pkg","build/dfu.zip", "-p", self.serial, "-b","115200"])
            if b"Device programmed." in out:
                    self.patchingSuccessful = True
                    return True
            else:
                self.patchingSuccessful = False
        else:
            self.patchingSuccessful = False

    def connect(self):
        if self.checkSupport("PATCH"):
            self.instantiateNrfutil()
            self.connected = True
            print("Interface connected !")
        elif self.checkSupport("LOG"):
            self.instantiateHci()
            self.connected = True
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
        pass
