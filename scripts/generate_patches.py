from pwnlib.asm import asm
import sys, os, subprocess
import re

def run(command):
    if isinstance(command, str):
        process = subprocess.Popen(command.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = process.communicate()
    return out,err


if len(sys.argv) < 5:
    print("Usage: "+sys.argv[0]+" <elf file> <symbols file> <rom file> <build dir> <dependencies>")
    exit(1)

elfFile = sys.argv[1]
symFile = sys.argv[2]
romFile = sys.argv[3]
buildDir = sys.argv[4]
dependencies = ["COMMON"]+sys.argv[5:]

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

missed_sections = []
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
                out,err = run(["arm-none-eabi-objcopy", elfFile, "--dump-section", sections[section]+"="+buildDir+"/section.bin"])
                if b"can't dump section" not in err:
                    # recover the code for that symbol
                    with open(buildDir+"/section.bin","rb") as content:
                        output_buffer = "ram,"+baseAddress+","+content.read().hex()+","+name+"\n"
                else:
                    missed_sections += [sections[section]]
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
                    output += "ram,"+baseAddress+","+zeros+","+name+"\n"
                else:
                    # dump the code for that symbol
                    out,err = run(["arm-none-eabi-objcopy", elfFile, "--dump-section", sections[section]+"."+name+"="+buildDir+"/section.bin"])
                    if b"can't dump section" not in err:
                        # recover the code for that symbol
                        with open(buildDir+"/section.bin","rb") as content:
                            output_buffer = "ram,"+baseAddress+","+content.read().hex()+","+name+"\n"

                        if section == "T" or section == "t":
                            functions[name] = baseAddress

                    else:
                        missed_sections += [(sections[section]+"."+name,baseAddress)]

            if sections[section]+"."+name not in written_sections:
                output += output_buffer
                written_sections += [sections[section]+"."+name]

if len(missed_sections) != 0:
    if all(list(map(lambda x: ".text.__" in x[0],missed_sections))):
        baseAddress = min([x[1] for x in missed_sections])
        print("LibGCC detected ! Dumping text section...")
        out,err = run(["arm-none-eabi-objcopy", elfFile, "--dump-section", ".text="+buildDir+"/section.bin"])
        if b"can't dump section" not in err:
            # recover the code for that symbol
            with open(buildDir+"/section.bin","rb") as content:
                output_buffer = "ram,"+baseAddress+","+content.read().hex()+",libgcc\n"
                output = output_buffer + output
        else:
           print("Failure, exiting...")
           exit(5)

output2 = ""
with open(romFile,"r") as f:
    rompatches = f.readlines()
    for rompatch in rompatches:
        rompatch = rompatch.replace("\n","").split(":")
        if len(rompatch) == 6:
            tag,section,name,baseAddress,target,instr = rompatch
            if tag in dependencies:
                baseAddress = "0x{:02x}".format(int(baseAddress,16))
                if name+"_hook" in functions:
                    instruction = "bl "+functions[name+"_hook"]
                    instruction = asm(instruction,arch="thumb",vma=int(baseAddress,16))
                    output2 += section+","+baseAddress+","+instruction.hex()+","+name+"\n"
        if len(rompatch) == 5:
            tag,section,name,baseAddress,instr = rompatch
            if len(instr) > 2 and instr[:2] == "0x":
                output2 += section+","+baseAddress+","+"{:08x}".format(int(instr,16))+","+name+"\n"
            else:
                instruction = asm(instr,arch="thumb",vma=int(baseAddress,16))
                output2 += section+","+baseAddress+","+instruction.hex()+","+name+"\n"

output = output + output2

if output != "":
    with open(buildDir+"/patches.csv","w") as f:
        f.write(output)
