import sys,os
from math import ceil, log

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
    start_offset = None
    last_written_addr = 0
    with open(input_hex_file, "r") as f:
        lines = f.readlines()
        for l in lines:

            l = bytes.fromhex(l.strip()[1:])
            size = l[0]
            addr = current_offset * 16 + int(l[1:3].hex(), 16)
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
        
    line = ":04000003{:04X}{:04X}".format(cs,ip)
    line += "{:02X}".format(checksum(line))
    output += line + "\n:00000001FF\n"    
    return output

def read(buf, so, address, length):
    return buf[address-so:address+length-so]

def write(buf, so, address, data):
    if len(buf)+so <= address:
        buf += b"\x00"*(address - (len(buf)+so)) + data
    else:
        buf = buf[:address-so]+ data + buf[address+len(data)-so:]
    return buf





if len(sys.argv) != 5:
    print("Usage: "+sys.argv[0]+" <input hex file> <patch file> <linker file> <output hex file>")
    exit(1)

inputHexFile = sys.argv[1]
patchFile = sys.argv[2]
if not os.path.isfile(patchFile):
    print("Patch file not found !")
    exit(2)
linkerFile = sys.argv[3]
outputHexFile = sys.argv[4]

# Get the address of the ram section
ramStart = None
codeStart = None
with open(linkerFile, "r") as f:
    lines = f.readlines()
    for l in lines:
        if "ram (rwx)" in l:
            l = l.strip()
            address = l.split("ORIGIN = ")[1].split(",")[0]
            ramStart = int(address, 16)
        if "flash (rwx" in l:
            l = l.strip()
            address = l.split("ORIGIN = ")[1].split(",")[0]
            codeStart = int(address, 16)

# Open inputHexFile
so, buffer, cs, ip = hexToInternal(inputHexFile)

with open(patchFile,"r") as f: 
    patches = [line.replace("\n","").split(",") for line in f.readlines()]

    for patch in patches:
        patchType, patchAddress, patchContent, name = patch
        patchAddress = int(patchAddress,16)
        if patchAddress >= ramStart:
            dataAddress = patchAddress - ramStart + 0x1e350
            print(hex(dataAddress), hex(codeStart), patch)
            if dataAddress + len(bytes.fromhex(patchContent)) >= codeStart:
                print("Data section overwrites the code section by", dataAddress + len(bytes.fromhex(patchContent)) - codeStart, "bytes")
                exit(1)
            buffer = write(buffer, so, dataAddress, bytes.fromhex(patchContent))
        else:
            buffer = write(buffer, so, patchAddress, bytes.fromhex(patchContent))

with open(outputHexFile, "w") as f:
    f.write(internalToHex(so, buffer, cs, ip))
