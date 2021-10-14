from pwnlib.asm import disasm
import sys,struct

if len(sys.argv) != 3:
	print("Usage: " + sys.argv[0]+ " <input patch configuration file> <output patch configuration file>")
	exit(1)

inputPatchConfigurationFile = sys.argv[1]
outputPatchConfigurationFile = sys.argv[2]

def switch_endianness(val):
	return struct.unpack(">I",struct.pack("I",val))[0]

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

inputHexFile = get_file_dir()+"/firmware.hex"

so,out,cs,ip = hexToInternal(inputHexFile)

hooks = ""
print("Extracting Stack Pointer init value from ISR vector... ",end="")
stackPointerInitValue = struct.unpack("I",out[0x1b000:0x1b004])[0]
print(hex(stackPointerInitValue))
print("Looking for hardcoded SP value...", end="")
currentValue = None
i=0
while currentValue != stackPointerInitValue:
	currentValue = struct.unpack("I",out[0x1b004+i:0x1b004+i+4])[0]
	i+=1
index = 0x1b004+i-1
print(hex(index))
hooks += "COMMON:rom:injected_stack_pointer_isr:0x1b000:0x{:08x}".format(switch_endianness(stackPointerInitValue-0x1000))
hooks += "\nCOMMON:rom:injected_stack_pointer_init:"+"0x{:08x}".format(index)+":0x{:08x}".format(switch_endianness(stackPointerInitValue-0x1000))

print("Adding hooks injected_stack_pointer_isr and injected_stack_pointer_init...")

print("Extracting ResetHandler address from ISR vector...",end="")
resetHandlerPointer = struct.unpack("I",out[0x1b004:0x1b008])[0] - 1
print(hex(resetHandlerPointer))

print("Disassembling ResetHandler to identify _mainCRTStartup call...",end="")
instructionToReplace = None
addressToReplace = None

i = 2
while i < 150:
	instructions = disasm(out[resetHandlerPointer:resetHandlerPointer+i],arch="thumb",vma=resetHandlerPointer)
	extractedInstructions = [(instruction[32:].split(" <")[0],instruction.split(":")[0]) for instruction in instructions.split("\n")]
	if len(extractedInstructions) > 1 and extractedInstructions[-1][0][:2] == "bl" and  extractedInstructions[-2][0][:2] == "bl":
		instructionToReplace = extractedInstructions[-1][0].replace("      "," 0x")
		addressToReplace = int(extractedInstructions[-1][1],16)
		print("found at "+"0x{:08x}".format(addressToReplace))
		break
	i += 2
if instructionToReplace is not None and addressToReplace is not None:
	print("Generating patch configuration file...")
	hooks += "\nCOMMON:rom:hook_init:""0x{:08x}".format(addressToReplace)+":on_init:"+instructionToReplace
	print("Adding hook on_init...")

	with open(inputPatchConfigurationFile,"r") as f:
		content = f.readlines()

	with open(outputPatchConfigurationFile,"w+") as f:
		f.write(hooks+"\n"+"".join(content))
