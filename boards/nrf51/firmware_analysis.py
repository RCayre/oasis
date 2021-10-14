from pwnlib.asm import disasm
import sys,struct

if len(sys.argv) != 2:
	print("Usage: " + sys.argv[0]+ " <information to extract>")
	exit(1)

info = sys.argv[1].upper()

def get_file_dir():
    return "/".join(__file__.split("/")[:-1])

# TODO: refactoring iHex manipulation tools
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

inputHexFile = get_file_dir() + "/firmware.hex"
so,out,cs,ip = hexToInternal(inputHexFile)

if info == "FIRMWARE_SIZE":
    print(hex(len(out)))
elif info == "MAX_RAM_ADDRESS":
    print(hex(struct.unpack("I",out[0x1b000:0x1b004])[0]))
