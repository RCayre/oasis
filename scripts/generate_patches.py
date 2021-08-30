from pwnlib.asm import asm
import sys, os, subprocess
import re

if len(sys.argv) != 5:
    print("Usage: "+sys.argv[0]+" <elf file> <symbols file> <rom file> <build dir>")
    exit(1)
    
elfFile = sys.argv[1]
symFile = sys.argv[2]
romFile = sys.argv[3]
buildDir = sys.argv[4]

if not os.path.isfile(elfFile):
    print("ELF file does not exist ")
    exit(2)

if not os.path.isfile(symFile):
    print("Symbol file does not exist ")
    exit(3)

if not os.path.isfile(romFile):
    print("ROM file does not exist ")
    exit(3)
        
sections = {
"T": ".text", 
"t": ".text",
"D": ".data",
"d": ".data",
"B": ".bss",
"b": ".bss",
"r": ".rodata"
}

included_sections = ["T", "t", "D", "d", "B", "b", "r"]

# Usually functions are placed in their own sections but they can sometimes
# have the same name. Then we only want to write the section once
written_sections = []

output = ""
functions = {}
with open(symFile,"r") as f:
    symbols = f.readlines()
    for symbol in symbols:
        # Get the section identifier
        regex = re.compile("\s[a-zA-Z]\s")
        section = regex.findall(symbol)[0].strip()

        output_buffer = ""
        # If it is a section to be included
        if section in included_sections:
            if section == "r":
                # .rodata
                baseAddress, section, name = symbol.replace("\n", "").split(" ")
                baseAddress = "0x{:02x}".format(int(baseAddress,16))
                # dump the code for that symbol
                subprocess.call(["arm-none-eabi-objcopy", elfFile, "--dump-section", sections[section]+"="+buildDir+"/section.bin"])
                # recover the code for that symbol
                with open(buildDir+"/section.bin","rb") as content:
                    output_buffer = "ram,"+baseAddress+","+content.read().hex()+","+name+"\n"
            else:
                # Exclude elements with no size
                if len(symbol.replace("\n", "").split(" ")) != 4:
                    continue

                # Anything other than .rodata and .bss
                baseAddress, size, section, name = symbol.replace("\n","").split(" ")
                baseAddress = "0x{:02x}".format(int(baseAddress,16))
                if section == "B" or section == "b":
                    # initialize with zeros
                    zeros = "".join(["00" for i in range(int(size, 16))])
                    output_buffer = "ram,"+baseAddress+","+zeros+","+name+"\n"
                else:
                    # dump the code for that symbol
                    subprocess.call(["arm-none-eabi-objcopy", elfFile, "--dump-section", sections[section]+"."+name+"="+buildDir+"/section.bin"])
                    # recover the code for that symbol
                    with open(buildDir+"/section.bin","rb") as content:
                        output_buffer = "ram,"+baseAddress+","+content.read().hex()+","+name+"\n"

                    if section == "T" or section == "t":
                        functions[name] = baseAddress
            if sections[section]+"."+name not in written_sections:
                output += output_buffer
                written_sections += [sections[section]+"."+name]

output2 = ""
with open(romFile,"r") as f:
    rompatches = f.readlines()
    for rompatch in rompatches:
        rompatch = rompatch.replace("\n","").split(":")
        if len(rompatch) == 4:
            name,baseAddress,target,instr = rompatch
            baseAddress = "0x{:02x}".format(int(baseAddress,16))
            if name+"_hook" in functions:
                instruction = "bl "+functions[name+"_hook"]
                instruction = asm(instruction,arch="thumb",vma=int(baseAddress,16))
                output2 += "rom,"+baseAddress+","+instruction.hex()+","+name+"\n"

output = output2 + output

if output != "":
    with open(buildDir+"/patches.csv","w") as f:
        f.write(output)


