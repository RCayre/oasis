#!/usr/bin/env python3 

from scapy.all import *

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class BTComm:
    def __init__(self,interface):
        self.btSocket = BluetoothHCISocket(int(interface[-1:]))
            
    def recv(self):
        pkt = self.btSocket.recv()
        if HCI_Event_Hdr in pkt and pkt.code == 0xFF:
            eventPayload = pkt.load
            index = 0

            if eventPayload[0] == 0xAA:
                # Handle user log
                header = bool(eventPayload[1])
                addr = ""
                if header == 1:
                    addr = ":".join(["{:02x}".format(i) for i in eventPayload[2:8]][::-1])
                
                data = " ".join(["{:02x}".format(i) for i in eventPayload[8:][::-1]])
                return (header, addr, data)
            elif eventPayload[0:2] == b"\x1b\x03":
                # Handle stack trace
                if eventPayload[2] == 0x2c:
                    data = eventPayload[4:]
                    values = [struct.unpack("<I", data[i:i+4])[0] for i in range(0, 64, 4)]
                    if data[0] == 0x02:
                        print(bcolors.BOLD + bcolors.FAIL + "Received Stack-Dump Event (contains %d registers):" % (data[1]))
                        registers = (
                            "pc: 0x%08x     lr: 0x%08x      sp:0x%08x       r0: 0x%08x      r1: 0x%08x\n"
                            % (values[2], values[3], values[1], values[4], values[5])
                        )
                        registers += (
                            "r2: 0x%08x     r3: 0x%08x      r4:0x%08x       r5: 0x%08x      r6: 0x%08x\n"
                            % (values[6], values[7], values[8], values[9], values[10])
                        )
                        print(bcolors.WARNING + registers + bcolors.ENDC)
        return None
        
interface = "hci0"
addressFilter = None
filterOnly = False
for argument in sys.argv:
    if "--interface=" in argument:
        interface = argument.split("--interface=")[1].lower()
    if "--filter=" in argument:
        addressFilter = argument.split("--filter=")[1].lower()
    if "--filter-only=" in argument:
        addressFilter = argument.split("--filter-only=")[1].lower()
        filterOnly = True

comm = BTComm(interface)
print("Listening to device on", interface, "...")
try:
    while True:
        pkt = comm.recv()
        if pkt is not None:
            header, addr, data = pkt
            if header == 1:
                # Skip messages with wrong address
                if addressFilter is not None and addressFilter != addr:
                    continue;
                print(bcolors.BOLD + bcolors.OKBLUE + addr + " : " + bcolors.ENDC, end="")
            else:
                # Also skip messages with no address if filter-only
                if filterOnly:
                    continue;
                print(bcolors.ENDC + bcolors.BOLD, end="")
            print(data + bcolors.ENDC)
except KeyboardInterrupt:
    exit() 
