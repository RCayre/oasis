from interface.interface import Interface
from internalblue.hcicore import HCICore
from internalblue.adbcore import ADBCore
import internalblue.hci as hci
from pwnlib.asm import disasm
from pwnlib import context
from queue import Queue
from utils import exec
import time

class InternalblueInterface(Interface):
    def getCompatibleHCIBoards(self):
        device_list = self.internalblue.device_list()
        compatible_device_list = []
        for dev in device_list:
            out,err = exec.execute_with_output("hciconfig -a "+dev[1])
            if b"Cypress" in out or b"Broadcom" in out:
                compatible_device_list.append(dev[1])
        return compatible_device_list

    def getADBBoards(self):
        device_list = self.internalblue.device_list()
        compatible_device_list = []
        for dev in device_list:
            compatible_device_list.append(dev[1])
        return compatible_device_list

    def instantiateInternalblue(self):
        self.interfaceNumber = 0

        if self.interface == "INTERNALBLUE_HCI":
            self.internalblue = HCICore()
        elif self.interface == "INTERNALBLUE_ADB":
            self.internalblue = ADBCore(serial=False)
        elif self.interface == "INTERNALBLUE_ADB_SERIAL":
            self.internalblue = ADBCore(serial=True)
        self.internalblue.log_level="ERROR"
        devices = self.getCompatibleHCIBoards() if "HCI" in self.interface else self.getADBBoards()
        try:
            self.internalblue.interface = devices[self.interfaceNumber]

        except:
            print("Interface error: interface not found !")
            exit(1)

    def __init__(self, target,interface=None, memoryZones=None):
        self.waiting = None
        self.receivedEvent = None

        if target is None: # partial instantiation to find memory zone during target generation
            self.memoryZones = memoryZones
            self.interface = interface.upper()
        else:
            Interface.__init__(self, target)

        self.eventQueue = Queue()
        self.instantiateInternalblue()


    def connect(self):
        if self.internalblue.connect():
            print("Interface connected !")
            self.connected = True
        else:
            print("Interface error: not connection to the target device.")
            exit(1)


    def sendHciCommand(self,opcode,data):
        answer = self.internalblue.sendHciCommand(opcode,data)
        if isinstance(answer,bytearray):
            answer = bytes(answer)
            return answer[0] == 0
        return False

    def listenSpecificEvent(self,opcode):
        self.internalblue.registerHciCallback(self.receiveHciCallback)
        self.waiting = opcode
        self.receivedEvent = None

    def waitSpecificEvent(self):
        while self.receivedEvent is None:
            time.sleep(0.1)
        event = self.receivedEvent
        self.receivedEvent
        return event

    def disconnect(self):
        if self.connected:
            self.internalblue.shutdown()
            self.connected = False

    def writeRam(self, address, value):
        return self.internalblue.writeMem(address,value)

    def writeRom(self, address, value):
        return self.internalblue.patchRom(address,value)

    def receiveHciCallback(self,record):
        try:
            hcipkt = record[0]  # get HCI Event packet
            if not issubclass(hcipkt.__class__, hci.HCI_Event):
                return
            if hcipkt.event_code == 0xFF:
                self.eventQueue.put(hcipkt.data)
            if hcipkt.event_code == self.waiting:
                self.receivedEvent = bytes(hcipkt.data)
                self.waiting = None

        except IndexError:
            pass

    def log(self):
        self.internalblue.registerHciCallback(self.receiveHciCallback)
        while True:
            yield self.eventQueue.get(block=True)

    def write(self, address, value):
        if self.memoryZones["rom"][0] <= address and address <= self.memoryZones["rom"][1]:
            return self.writeRom(address,value)
        else:
            return self.writeRam(address,value)

    def patchRam(self, address, value):
        return self.writeRam(address,value)


    def patchRom(self, address, value):
        return self.writeRom(address,value)

    def patch(self, address, value):
        return self.write(address, value)

    def read(self,address,length):
        return self.internalblue.readMem(address,length)

    def findFreeZone(self,size,strategy="PATCHRAM"):
        if strategy == "PATCHRAM":
            print("Trying to find free zone using PATCHRAM strategy... ("+hex(size)+")")
            # find patchram zones
            (target_addresses,new_values, enabled_bitmap) = self.internalblue.getPatchramState()
            freeSlots = []
            functionsAddresses = []
            for i in range(len(target_addresses)):
                if enabled_bitmap[i] == 1:
                    instruction = disasm(new_values[i],arch="thumb",vma=target_addresses[i])
                    if "b.w" in instruction:
                        functionsAddresses.append(int(instruction.split()[-2],16))
                else:
                    freeSlots.append(i)

            # Establish the zones used by ram patches
            functionsAddresses = sorted(functionsAddresses)
            if len(functionsAddresses) == 0:
                return None
            zoneStart = [functionsAddresses[0]]
            zoneEnd = []
            previousAddress = zoneStart[0]
            for address in functionsAddresses[1:]:
                if previousAddress+4096 < address:
                    zoneEnd.append(previousAddress)
                    zoneStart.append(address)
                previousAddress = address

            if len(zoneEnd) == len(zoneStart) - 1:
                zoneEnd.append(functionsAddresses[-1])
            # Use last zone end
            return zoneEnd[-1]+1024

        elif strategy == "BLOC":
            print("Trying to find free zone using BLOC strategy... ("+hex(size)+")")

            # find large enough BLOC
            blocks = [block for block in self.internalblue.readHeapInformation() if block["capacity"] == block["list_length"]] # only keep unused blocks
            blocks = sorted(blocks, key=lambda d: d['memory_size'])[::-1] # sort them by available memory size
            for block in blocks:
                if size <= block["memory_size"]-4:
                    return block["memory"]+4
            return None
        return None
