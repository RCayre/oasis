from oasis.utils import patch_parser,conf_parser,dissectors,wireshark
from oasis.interface import openocd,internalblue,nrfutil
from scapy.all import BTLE_ADV, BTLE_DATA, BTLE
import sys,time,struct

def getInterface(target):
    interfaceType = conf_parser.getTargetInterface(target)
    if "INTERNALBLUE" in interfaceType:
        interface = internalblue.InternalblueInterface(target)
    elif "OPENOCD" in interfaceType:
        interface = openocd.OpenocdInterface(target)
    elif "NRFUTIL" in interfaceType:
        interface = nrfutil.NRFUtilInterface(target)
    return interface

def read(address,size,target):
    interface = getInterface(target)
    if not interface.checkSupport("READ"):
        print("Interface does not support reading.")
        exit(1)
    interface.connect()
    print(interface.read(address,size).hex())
    interface.disconnect()

def monitor(address,size,target):
    interface = getInterface(target)
    if not interface.checkSupport("READ"):
        print("Interface does not support reading.")
        exit(1)
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


def interact(command, target, params=[]):
    if command == "log":
        interface = getInterface(target)
        if not interface.checkSupport("LOG"):
            print("Interface does not support logging.")
            exit(1)

        interface.connect()
        sys.stdout.flush()
        sys.stderr.flush()
        if len(params) > 0:
            with open(params[0], "a") as f:
                f.write("Log started !\n")
        try:
            for log in interface.log():
                msg = dissectors.parse_log_message(log)
                try:
                    log_line = "<"+target+"> ["+str(time.time())+"] "+msg
                    print(log_line)
                    if len(params) > 0:
                        with open(params[0], "a") as f:
                            f.write(log_line+"\n")
                except TypeError:
                    pass
                sys.stdout.flush()
                sys.stderr.flush()

        except KeyboardInterrupt:
            interface.disconnect()
            exit(0)

        except KeyboardInterrupt:
            interface.disconnect()
            exit(0)

    if command == "wireshark":
        interface = getInterface(target)
        if not interface.checkSupport("LOG"):
            print("Interface does not support logging.")
            exit(1)

        interface.connect()
        sys.stdout.flush()
        sys.stderr.flush()
        if len(params) > 0:
            ws = wireshark.WiresharkStream(params[0])
        else:
            ws = wireshark.WiresharkStream()

        try:
            for log in interface.log():
                access_address = 0x11223344 # fake access address if we miss the conn_init  event
                msg = dissectors.parse_log_message(log,formatting=False)
                if msg["type"] == "SCAN_RX":
                    log_line = "<"+target+"> ["+str(time.time())+"] "+repr(BTLE_ADV(msg["packet"]))
                    ws.write(BTLE()/BTLE_ADV(msg["packet"]))
                elif msg["type"] == "CONN_RX":
                    log_line = "<"+target+"> ["+str(time.time())+"] "+repr(BTLE_DATA(msg["packet"]))
                    ws.write(BTLE(access_addr=access_address)/BTLE_DATA(msg["packet"]))
                elif msg["type"] == "CONN_INIT":
                    access_address = int(msg["access_address"],16)

                sys.stdout.flush()
                sys.stderr.flush()

        except KeyboardInterrupt:
            interface.disconnect()
            exit(0)

        except KeyboardInterrupt:
            interface.disconnect()
            exit(0)

    elif command == "read" or command == "monitor":
        if len(params) < 1:
            print("Please provide a symbol or an address to read.")
            exit(2)
        information = params[0]
        address = None
        size = None
        if information.startswith("0x"):
            address = int(information,16)
            if len(params) == 2:
                try:
                    size = int(params[1])
                except:
                    print("Please provide a valid size.")
                    exit(4)
            else:
                size = 4
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
                read(address,size,target)
            elif command == "monitor":
                monitor(address,size,target)

    elif command == "start-scan":
        interface = getInterface(target)
        if not interface.checkSupport("HCI_COMMAND"):
            print("Interface does not support HCI commands.")
            exit(1)
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
        interface = getInterface(target)
        if not interface.checkSupport("HCI_COMMAND"):
            print("Interface does not support HCI commands.")
            exit(1)
        interface.connect()

        if interface.sendHciCommand(0x200c,bytes.fromhex("0001")): # set scan enable
            print("Set Scan Enable OK")
        else:
            print("Error during Set Scan Enable")
        interface.disconnect()

    elif command == "connect":
        if len(params) < 1:
            print("Please provide an address.")
            exit(2)
        if len(params) == 1:
            address = params[0].upper()
            addressType = "public"
        elif len(params) == 2:
            address = params[0].upper()
            addressType = params[1].lower() if params[1].lower() in ("public","random") else "public"

        addressBytes = bytes.fromhex(address.replace(":",""))[::-1]
        interface = getInterface(target)
        if not interface.checkSupport("HCI_COMMAND"):
            print("Interface does not support HCI commands.")
            exit(1)
        interface.connect()
        interface.listenSpecificHciEvent(0x3e)
        if interface.sendHciCommand(0x200D,b"\x60\x00\x30\x00\x00" + (b"\x00" if addressType == "public" else b"\x01") + addressBytes + b"\x01\x18\x00\x28\x00\x00\x00\xd0\x07\x00\x00\x00\x00"): # start connection
            print("Start Connection OK")
            event = interface.waitSpecificHciEvent(timeout=3)
            if event is not None and (event[0] == 0x0a or event[0] == 0x01): # LE Enhanced Connection Complete or LE Connection Complete
                success = event[1] == 0x00
                handle = struct.unpack("H",event[2:4])[0]
                print("Connection established - handle = "+str(handle) if success else "Connection failed")
            else:
                print("Connection failed")

        interface.disconnect()

    elif command == "disconnect":
        if len(params) < 1:
            print("Please provide the connection handle.")
            exit(2)
        if len(params) == 1:
            if "0x" in params[0]:
                handle = int(params[0],16)
            else:
                handle = int(params[0])

            interface = getInterface(target)
            if not interface.checkSupport("HCI_COMMAND"):
                print("Interface does not support HCI commands.")
                exit(1)
            interface.connect()
            if interface.sendHciCommand(0x406,struct.pack("H",handle)+b"\x13"):
                print("Stop connection OK")
            interface.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: "+sys.argv[0]+" <target> <command>")
        print("Commands: read <symbol>")
        print("Commands: read <address>")
        print("Commands: read <address> <size>")
        print("Commands: monitor <symbol>")
        print("Commands: monitor <address>")
        print("Commands: monitor <address> <size>")
        print("Commands: log [filename]")
        print("Commands: wireshark [filename]")
        print("Commands: start-scan")
        print("Commands: stop-scan")
        print("Commands: connect <address>")
        print("Commands: connect <address> <address_type>")
        print("Commands: disconnect <handle>")

        exit(1)


    target = sys.argv[1]
    command = sys.argv[2].lower()
    interact(command, target, sys.argv[3:])
