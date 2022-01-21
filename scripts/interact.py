from utils import patch_parser,conf_parser,test
from interface import openocd,internalblue
import sys,time,struct

if len(sys.argv) < 3:
    print("Usage: "+sys.argv[0]+" <target> <command>")
    print("Commands: read <symbol>")
    print("Commands: read <address>")
    print("Commands: read <address> <size>")
    print("Commands: monitor <symbol>")
    print("Commands: monitor <address>")
    print("Commands: monitor <address> <size>")
    print("Commands: log")
    print("Commands: run-test")
    print("Commands: start-scan")
    print("Commands: stop-scan")
    print("Commands: connect <address>")
    print("Commands: connect <address> <address_type>")

    exit(1)

target = sys.argv[1]
command = sys.argv[2].lower()

def getInterface():
    interfaceType = conf_parser.getTargetInterface(target)
    if "INTERNALBLUE" in interfaceType:
        interface = internalblue.InternalblueInterface(target)
    else:
        interface = openocd.OpenocdInterface(target)
    return interface

def read(address,value):
    interface = getInterface()
    interface.connect()
    print(interface.read(address,size).hex())
    interface.disconnect()

def monitor(address,value):
    interface = getInterface()
    interface.connect()
    value = b""
    printedValue = b""
    try:
        while True:
            value = interface.read(address,size)
            if value != printedValue:
                printedValue = value
                print(printedValue.hex())
                sys.stdout.flush()
                sys.stderr.flush()
    except KeyboardInterrupt:
        interface.disconnect()


if command == "log":
    interface = getInterface()
    interface.connect()
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        for log in interface.log():
            print("<"+target+"> ["+str(time.time())+"] "+log.hex())
            sys.stdout.flush()
            sys.stderr.flush()

    except KeyboardInterrupt:
        interface.disconnect()
        exit(0)

elif command == "run-test":
    interface = getInterface()
    interface.connect()
    try:
        for log in interface.log():
            msg = test.parse_test_message(log)
            if msg is not None:
                test.show_test_message(msg)
    except KeyboardInterrupt:
        interface.disconnect()
        exit(0)


elif command == "read" or command == "monitor":
    if len(sys.argv) < 4:
        print("Please provide a symbol or an address to read.")
        exit(2)
    information = sys.argv[3]
    address = None
    size = None
    if information.startswith("0x"):
        address = int(information,16)
        if len(sys.argv) == 5:
            try:
                size = int(sys.argv[4])
            except:
                print("Please provide a valid size.")
                exit(4)
    else:
        patches = patch_parser.getMapping(target)
        if patches is None:
            print("Mapping file not found.")
            exit(3)
        for patch in patches:
            if patch["patch_name"] == information:
                address = patch["patch_address"]
                size = len(patch["patch_content"])
                break
        if address is None and size is None:
            print("Symbol not found.")
            exit(5)
    if address is not None and size is not None:
        if command == "read":
            read(address,size)
        elif command == "monitor":
            monitor(address,size)
elif command == "start-scan":
    interface = getInterface()
    interface.connect()
    if interface.sendHciCommand(0x200b,bytes.fromhex("00002000200000")): # set scan parameters
        print("Set Scan Parameters OK")
    else:
        print("Error during Set Scan Parameters")

    if interface.sendHciCommand(0x200c,bytes.fromhex("0101")): # set scan enable
        print("Set Scan Enable OK")
    else:
        print("Error during Set Scan Enable")

    interface.disconnect()
elif command == "stop-scan":
    interface = getInterface()
    interface.connect()

    if interface.sendHciCommand(0x200c,bytes.fromhex("0001")): # set scan enable
        print("Set Scan Enable OK")
    else:
        print("Error during Set Scan Enable")
    interface.disconnect()

elif command == "connect":
    if len(sys.argv) < 4:
        print("Please provide an address.")
        exit(2)
    if len(sys.argv) == 4:
        address = sys.argv[3].upper()
        addressType = "public"
    elif len(sys.argv) == 5:
        address = sys.argv[3].upper()
        addressType = sys.argv[4].lower() if sys.argv[4].lower() in ("public","random") else "public"

    addressBytes = bytes.fromhex(address.replace(":",""))[::-1]
    interface = getInterface()
    interface.connect()
    interface.listenSpecificEvent(0x3e)
    if interface.sendHciCommand(0x200D,b"\x60\x00\x30\x00\x00" + (b"\x00" if addressType == "public" else b"\x01") + addressBytes + b"\x01\x18\x00\x28\x00\x00\x00\xd0\x07\x00\x00\x00\x00"): # start connection
        print("Start Connection OK")
        event = interface.waitSpecificEvent()
        if event[0] == 0x0a or event[0] == 0x01: # LE Enhanced Connection Complete or LE Connection Complete
            success = event[1] == 0x00
            handle = struct.unpack("H",event[2:4])[0]
            print("Connection established - handle = "+str(handle) if success else "Connection failed")
    interface.disconnect()

elif command == "disconnect":
    if len(sys.argv) < 4:
        print("Please provide the connection handle.")
        exit(2)
    if len(sys.argv) == 4:
        if "0x" in sys.argv[3]:
            handle = int(sys.argv[3],16)
        else:
            handle = int(sys.argv[3])

        interface = getInterface()
        interface.connect()
        if interface.sendHciCommand(0x406,struct.pack("H",handle)+b"\x13"):
            print("Stop connection OK")
        interface.disconnect()
