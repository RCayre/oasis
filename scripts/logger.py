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
    def __init__(self,interface="hci1"):
        self.btSocket = BluetoothHCISocket(int(interface[-1:]))
            
    def recv(self):
        pkt = self.btSocket.recv()
        if HCI_Event_Hdr in pkt and pkt.code == 0xFF:
            eventPayload = pkt.load
            index = 0

            if eventPayload[0] != 0xAA:
                return None

            header = bool(eventPayload[1])
            addr = ""
            if header == 1:
                addr = ":".join(["{:02x}".format(i) for i in eventPayload[2:8]][::-1])
            
            data = " ".join(["{:02x}".format(i) for i in eventPayload[8:][::-1]])
            return (header, addr, data)
        return None
        
addressFilter = None
filterOnly = False
for argument in sys.argv:
    if "--filter=" in argument:
        addressFilter = argument.split("--filter=")[1].lower()
    if "--filter-only=" in argument:
        addressFilter = argument.split("--filter-only=")[1].lower()
        filterOnly = True

comm = BTComm()
print("Listening to device...")
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
                print(bcolors.WARNING, end="")
            print(data + bcolors.ENDC)
except KeyboardInterrupt:
    exit() 
