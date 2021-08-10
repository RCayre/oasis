from pwnlib.asm import asm
import sys, os, subprocess

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
"D": ".data",
"B": ".bss"
}

output = ""
functions = {}
with open(symFile,"r") as f:
	symbols = f.readlines()
	for symbol in symbols:
		if " A " not in symbol and " a " not in symbol:
			baseAddress, size, section, name = symbol.replace("\n","").split(" ")
			baseAddress = "0x{:02x}".format(int(baseAddress,16))
			if section != "B":
				subprocess.call(["arm-none-eabi-objcopy", elfFile, "--dump-section", sections[section]+"."+name+"="+buildDir+"/section.bin"])
				with open(buildDir+"/section.bin","rb") as content:
					output += "ram,"+baseAddress+","+content.read().hex()+","+name+"\n"
			if section == "T":
				functions[name] = baseAddress

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


