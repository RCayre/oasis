from internalblue.hcicore import HCICore
from internalblue.adbcore import ADBCore
import sys,os

if len(sys.argv) != 3:
    print("Usage: "+sys.argv[0]+" <patch file> <core type>")
    exit(1)

if not os.path.isfile(sys.argv[1]):
    print("Patch file not found !")
    exit(2)
if not sys.argv[2] in ("ADB_SERIAL","ADB","HCI"):
    print("Core type not found !")
    exit(3)
with open(sys.argv[1],"r") as f:
    patches = [line.replace("\n","").split(",") for line in f.readlines()]

    if sys.argv[2] == "ADB_SERIAL":
        internalblue = ADBCore(serial=True)
    elif sys.argv[2] == "ADB":
        internalblue = ADBCore(serial=False)
    else:
        internalblue = HCICore()

    device_list = internalblue.device_list()
    if len(device_list) == 0:
        internalblue.logger.warning("No devices connected!")
        exit(-1)
    internalblue.interface = device_list[0][1]

    # setup sockets
    if not internalblue.connect():
        internalblue.logger.critical("No connection to target device.")
        exit(-1)

    for patch in patches:
        patchType, patchAddress, patchContent, name = patch
        patchAddress = int(patchAddress,16)
        if patchType == "rom":
            print("[ROM] Writing "+name+" at "+"0x{:02x}".format(patchAddress)+"...",end="")
            if not internalblue.patchRom(patchAddress,bytes.fromhex(patchContent)):
                print("KO")
            else:
                print("OK")
        elif patchType == "ram":
            print("[RAM] Writing "+name+" at "+"0x{:02x}".format(patchAddress)+"...",end="")
            if not internalblue.writeMem(patchAddress,bytes.fromhex(patchContent)):
                print("KO")
            else:
                print("OK")

    # shutdown connection
    internalblue.shutdown()
    internalblue.logger.info("Goodbye")
