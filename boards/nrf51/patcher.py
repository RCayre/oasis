import sys,os
from math import ceil, log
import subprocess

def checksum(line):
    line = bytes.fromhex(line[1:])
    s = 0
    for v in line:
        s += v
    return 0xFF & (0xff - (0xff & s) + 1)

def hexToInternal(input_hex_file):
    output = b""
    # Intel HEX to bytes
    code_segment = None
    instruction_pointer = None
    current_offset = 0
    msb = 0
    start_offset = None
    last_written_addr = 0
    with open(input_hex_file, "r") as f:
        lines = f.readlines()
        for l in lines:
            l = bytes.fromhex(l.strip()[1:])
            size = l[0]
            addr = (msb << 16) | (current_offset * 16 + int(l[1:3].hex(), 16))
            type = l[3]
            data = l[4:-1].hex()
            checksum = l[-1]

            # If data
            if type == 0:
                if start_offset is None:
                    start_offset = addr
                # If there was a gap between addresses, fill with zeros
                if last_written_addr != addr - 1 and last_written_addr != 0:
                    output += bytes.fromhex("00" * (addr - last_written_addr))
                last_written_addr = addr + size

                # Add the data
                output += bytes.fromhex(data)
            elif type == 2:
                # Change the current offset
                current_offset = int(data, 16)
            elif type == 3:
                code_segment = int(data[:4],16)
                instruction_pointer = int(data[4:],16)
            elif type == 4:
                # Change the current msb
                msb = int(data, 16)
    return (start_offset, output, code_segment, instruction_pointer)

def internalToHex(start_offset, internal, cs, ip):
    output = ""

    current_offset = 0
    for i in range(0, len(internal), 16):
        # If the address doesn't fit in the 4 bytes, add the offset
        if i + start_offset - current_offset > 0xFFFF:
            current_offset = i + start_offset
            size = ceil(log(i, 2)) // 8
            line = ":{:02X}000002{:04X}".format(size,(start_offset + i) // 16)
            line += "{:02X}".format(checksum(line))

            output += line + "\n"

        line = ":{:02X}{:04X}00{}".format(len(internal[i:i+16]), i + start_offset - current_offset, internal[i:i+16].hex().upper())
        line += "{:02X}".format(checksum(line))

        output += line + "\n"

    if cs is not None and ip is not None:
        line = ":04000003{:04X}{:04X}".format(cs,ip)
        line += "{:02X}".format(checksum(line))
        output += line + "\n:00000001FF\n"
    else:
        line = ":00000001FF\n"
        output += line
    return output

def read(buf, so, address, length):
    return buf[address-so:address+length-so]

def write(buf, so, address, data):
    if len(buf)+so <= address:
        buf += b"\x00"*(address - (len(buf)+so)) + data
    else:
        buf = buf[:address-so]+ data + buf[address+len(data)-so:]
    return buf

def get_file_dir():
    return "/".join(__file__.split("/")[:-1])

def run(command):
    if isinstance(command, str):
        process = subprocess.Popen(command.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = process.communicate()
    return out,err




if len(sys.argv) != 6:
    print("Usage: "+sys.argv[0]+" <patch file> <code start> <code length> <ram start> <ram length>")
    exit(1)

patchFile = sys.argv[1]
inputHexFile = get_file_dir() + "/firmware.hex"
outputHexFile = "build/out.hex"

flashingMethod = "NRFJPROG"

# Get the address of the ram section
codeStart = int(sys.argv[2],16)
codeLength = int(sys.argv[3],16)
ramStart = int(sys.argv[4],16)
ramLength = int(sys.argv[5],16)

# Open inputHexFile
so, buffer, cs, ip = hexToInternal(inputHexFile)
try:
    with open(patchFile,"r") as f:
        patches = [line.replace("\n","").split(",") for line in f.readlines()]

        for patch in patches:
            patchType, patchAddress, patchContent, name = patch
            patchAddress = int(patchAddress,16)
            if patchAddress >= ramStart:
                dataAddress = patchAddress - ramStart + (codeStart - ramLength)
                print("[RAM] Writing " + name + " at " + hex(dataAddress) + "...",end="")
                if dataAddress + len(bytes.fromhex(patchContent)) >= codeStart:
                    print("KO")
                    print("Data section overwrites the code section by", dataAddress + len(bytes.fromhex(patchContent)) - codeStart, "bytes")
                    exit(1)
                else:
                    try:
                        buffer = write(buffer, so, dataAddress, bytes.fromhex(patchContent))
                        print("OK")
                    except:
                        print("KO")
            else:
                print("[ROM] Writing " + name + " at " + hex(patchAddress) + "...",end="")
                try:
                    buffer = write(buffer, so, patchAddress, bytes.fromhex(patchContent))
                    print("OK")
                except:
                    print("KO")
            sys.stdout.flush()
except FileNotFoundError:
    print("Patch file not found, exiting ...")
    exit(3)
with open(outputHexFile, "w") as f:
    f.write(internalToHex(so, buffer, cs, ip))

print("Flashing device ...")
if flashingMethod == "OPENOCD":
    out,err = run(["openocd","-f","interface/stlink.cfg","-f","target/nrf51.cfg","-c","init","-c", "reset init", "-c","halt", "-c" ,"nrf51 mass_erase", "-c" ,"program build/out.hex verify", "-c","reset","-c","exit"])
    if b"Verified OK" not in err:
        print("Error while flashing the device")
        exit(4)

elif flashingMethod == "NRFJPROG":
    out,err = run("nrfjprog --program build/out.hex -f nrf51 --chiperase")
    out2,err2 = run("nrfjprog --reset -f nrf51")
    if b"Verified OK" not in out and b"Run" not in out2:
        print("Error while flashing the device")
        exit(4)
print("Flashing successfull :)")
