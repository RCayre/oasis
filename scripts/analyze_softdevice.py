import sys,struct,threading
from pwnlib.asm import disasm
import multiprocessing
import signal

if len(sys.argv) != 2:
    print("Usage: "+sys.argv[0]+ " <HEX firmware>")
    exit(1)

inputHexFile = sys.argv[1]

def findScalarsInRange(dump,minAddress,maxAddress,minValue,maxValue):
    for i in range(minAddress,maxAddress-4,2):
        value = struct.unpack("I",out[i:i+4])[0]
        if value >= minValue and value <= maxValue:
           yield (value,i)

def findScalarCrossReferences(dump,minAddress,maxAddress,addresses):
    try:
        for i in range(minAddress,maxAddress-4,2):
            twoBytesInstruction = disasm(dump[i:i+2],arch="thumb",vma=i)
            if "ldr" in twoBytesInstruction and "; (" in twoBytesInstruction and int(twoBytesInstruction.split("; (")[1].split(" ")[0],16) in addresses:
                print("Read access at",hex(i),"to",hex(int(twoBytesInstruction.split("; (")[1].split(" ")[0],16)))
                print(twoBytesInstruction)

            else:
                fourBytesInstruction = disasm(dump[i:i+4],arch="thumb",vma=i)
                if "str" in fourBytesInstruction and "; (" in fourBytesInstruction and int(fourBytesInstruction.split("; (")[1].split(" ")[0],16) in addresses:
                    print("Write access at",hex(i),"to",hex(int(fourBytesInstruction.split("; (")[1].split(" ")[0],16)))
                    print(fourBytesInstruction)
    except KeyboardInterrupt:
        return

def findFunctions(dump, minAddress, maxAddress):
    i = 0
    functions = {}
    currentFunctionAddress = None
    currentFunction = ""

    while i < maxAddress-4:
        if currentFunctionAddress is None:
            twoBytesInstruction = disasm(dump[i:i+2],arch="thumb",vma=i)
            fourBytesInstruction = disasm(dump[i:i+4],arch="thumb",vma=i)
            if ("push" in twoBytesInstruction and "lr" in twoBytesInstruction) or ("push" in fourBytesInstruction and "lr" in fourBytesInstruction):
                currentFunctionAddress = i
        else:
            currentFunction = disasm(dump[currentFunctionAddress:i+2])
            if ("pop" in currentFunction.split("\n")[::-1] and "pc" in currentFunction.split("\n")[::-1]) or  ("bx" in currentFunction.split("\n")[::-1] and "lr" in currentFunction.split("\n")[::-1])  or ("pop" in currentFunction.split("\n")[::-1] and "pc" in currentFunction.split("\n")[::-1]) :
                functions[currentFunctionAddress] = currentFunction
                currentFunction = ""
                currentFunctionAddress = None
        i+=2
    return functions

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

so,out,cs,ip = hexToInternal(inputHexFile)
radioRegisters = {address : value  for value,address in findScalarsInRange(out,0,len(out),0x40001000,0x40001FFF)}
radioRegistersAddresses = radioRegisters.keys()
print(findFunctions(out,0x1000,0x1B000))
#findScalarCrossReferences(out, 0x1000,0x1B000,radioRegistersAddresses)
'''
startOffset    =    0xB000
startApp       =    0x1B000
nbThreads = 32
value = ((startApp-startOffset)//nbThreads)

jobs = []
try:
    for i in range(nbThreads):
        p = multiprocessing.Process(target=findScalarCrossReferences, args=(out,startOffset+i*value,startOffset+(i+1)*value,radioRegistersAddresses))
        jobs.append(p)
        p.start()
except (KeyboardInterrupt,SystemExit):
    for j in jobs:
        j.terminate()
'''
