from internalblue.hcicore import HCICore
import sys,os

if len(sys.argv) != 2:
    print("Usage: "+sys.argv[0]+" <patch file>")
    exit(1)

if not os.path.isfile(sys.argv[1]):
    print("Patch file not found !")
    exit(2)
with open(sys.argv[1],"r") as f: 
    patches = [line.replace("\n","").split(",") for line in f.readlines()]

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
            print("[PATCHROM] Writing "+name+" at "+"0x{:02x}".format(patchAddress)+"...",end="")
            if not internalblue.patchRom(patchAddress,bytes.fromhex(patchContent)):
                print("KO")
            else:
                print("OK")
        elif patchType == "ram":
            print("[WRITERAM] Writing "+name+" at "+"0x{:02x}".format(patchAddress)+"...",end="")
            if not internalblue.writeMem(patchAddress,bytes.fromhex(patchContent)):
                print("KO")
            else:
                print("OK")

    # shutdown connection
    internalblue.shutdown()
    internalblue.logger.info("Goodbye")

