from oasis.interface.interface import Interface
from internalblue.hcicore import HCICore
from internalblue.adbcore import ADBCore
import internalblue.hci
from queue import Queue
from oasis.controllers.analysis import thumb
from oasis.utils import exec,hci
import time

class InternalblueInterface(Interface):
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
        devices = hci.listCompatibleHciInterfaces([(305, None), (15, None)]) if "HCI" in self.interface else self.getADBBoards()
        try:
            self.internalblue.interface = devices[self.interfaceNumber]

        except:
            print("Interface error: interface not found !")
            exit(1)

    def __init__(self, target,interface=None, memoryZones=None):
        self.waiting = None
        self.patches = []
        self.receivedEvent = None

        if target is None: # partial instantiation to find memory zone during target generation
            self.memoryZones = memoryZones
            self.interface = interface.upper()
        else:
            Interface.__init__(self, target)

        self.eventQueue = Queue()
        self.instantiateInternalblue()

    def checkSupport(self,feature):
        if feature == "PATCH" or feature =="LOG" or feature == "READ" or feature == "WRITE" or feature == "FIND_MEMORY_ZONE" or feature == "HCI_COMMAND":
            return "ADB" in self.interface and len(self.getADBBoards()) > 0 or "HCI" in self.interface and len(hci.listCompatibleHciInterfaces([(305, None), (15, None)])) > 0

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
            return answer[-1] == 0

        return False

    def listenSpecificHciEvent(self,opcode):
        self.internalblue.registerHciCallback(self.receiveHciCallback)
        self.waiting = opcode
        self.receivedEvent = None

    def waitSpecificHciEvent(self,timeout=None):
        maxTime = time.time() + timeout
        while self.receivedEvent is None and (timeout is None or time.time() <= maxTime):
            time.sleep(0.1)
        event = self.receivedEvent
        self.receivedEvent = None
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
            if not issubclass(hcipkt.__class__, internalblue.hci.HCI_Event):
                return
            if hcipkt.event_code == 0xFF:
                self.eventQueue.put(hcipkt.data)
            if hcipkt.event_code == self.waiting:
                self.receivedEvent = bytes(hcipkt.data)
                self.waiting = None

        except IndexError:
            pass

    def isPatchingSuccessful(self):
        return all(self.patches)

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
        success = self.write(address, value)
        self.patches.append(success)
        return success

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

                    instruction = list(thumb.exploreInstructions(thumb.disassemble(new_values[i],offset=target_addresses[i])))[0]
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
