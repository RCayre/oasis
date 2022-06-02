import os, os.path
from oasis.utils import exec,patch_parser,conf_parser
from string import Template
from oasis.controllers.analysis.reverse import asm
import re, struct

TRAMPOLINE_ARM_FUNCTION = """
__attribute__((optimize("O0")))
__attribute__((naked))
void $name() {
	__asm__(
	"push {r0-r3,lr}\\n\\t"
	"bl $target_function\\n\\t"
	"pop {r0-r3}\\n\\t"
	"$instruction\\n\\t"
	"pop {pc}\\n\\t");
}
"""

def getBuildDirectory():
    buildDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../../build")
    return buildDirectory

def getPatchedHexFirmware():
    return getBuildDirectory()+"/firmware.hex"

def buildPatchedHexFirmware(content):
    directory = getBuildDirectory()
    with open(directory+"/firmware.hex","w") as f:
        f.write(content)

def generateTrampolineFunction(name,target_function,instruction, architecture="arm"):
	if "arm" in architecture or "thumb" in architecture:
	    template = Template(TRAMPOLINE_ARM_FUNCTION)
	    return template.substitute(name=name+"_trampoline", target_function=target_function,instruction=instruction)

def generateTrampolineFile(patchesList, dependencies, architecture="arm"):
    content = ""
    for patch in patchesList:
        if patch["type"] == "function_hook" and patch["dependency"] in dependencies:
            content += generateTrampolineFunction(patch["name"], patch["target_function"],patch["instruction"],  architecture=architecture)
    with open(getBuildDirectory()+"/trampolines.c", "w") as f:
        f.write(content)

def generateJump(address,vma, architecture="arm"):
	if "arm" in architecture or "thumb" in architecture:
		instruction = "bl "+address
		instruction = asm(instruction,arch="thumb",vma=vma)
		return instruction

def generatePatchesFile(target, dependencies):
	buildDirectory = getBuildDirectory()
	architecture = conf_parser.getTargetArchitecture(target)

	symbolsFile = buildDirectory+"/symbols.sym"
	elfFile = buildDirectory+"/out.elf"

	sections = {
		"t": ".text",
		"T": ".text",
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
	functions = {}
	output = ""
	with open(symbolsFile,"r") as f:
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
					out,err = exec.execute_with_output([conf_parser.getObjcopy(architecture), elfFile, "--dump-section", sections[section]+"="+buildDirectory+"/section.bin"])
					if b"can't dump section" not in err:
						# recover the code for that symbol
						with open(buildDirectory+"/section.bin","rb") as content:
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
						out,err = exec.execute_with_output([conf_parser.getObjcopy(architecture), elfFile, "--dump-section", sections[section]+"."+name+"="+buildDirectory+"/section.bin"])
						if b"can't dump section" not in err:
							# recover the code for that symbol
							with open(buildDirectory+"/section.bin","rb") as content:
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
	        out,err = exec.execute_with_output([conf_parser.getObjcopy(architecture), elfFile, "--dump-section", ".text="+buildDirectory+"/section.bin"])
	        if b"can't dump section" not in err:
	            # recover the code for that symbol
	            with open(buildDirectory+"/section.bin","rb") as content:
	                output_buffer = "ram,"+baseAddress+","+content.read().hex()+",libgcc\n"
	                output = output_buffer + output
	        else:
	           print("Failure, exiting...")
	           exit(1)

	targetPatches = patch_parser.getTargetPatches(target)
	for patch in targetPatches:
		if patch["dependency"] in dependencies:
			if patch["type"] == "function_hook" and patch["name"]+"_trampoline" in functions:
				instruction = generateJump(functions[patch["name"]+"_trampoline"],patch["address"], architecture=architecture)
				output += patch["section"]+","+"0x{:02x}".format(patch["address"])+","+instruction.hex()+","+patch["name"]+"\n"
			elif patch["type"] == "function_pointer" and patch["function_pointer"] in functions:
				output += patch["section"]+","+"0x{:02x}".format(patch["address"])+","+struct.pack("I",int(functions[patch["function_pointer"]],16)+1).hex() +","+patch["name"]+"_PTR"+"\n"
			elif patch["type"] == "value":
				output += patch["section"]+","+"0x{:02x}".format(patch["address"])+","+"{:08x}".format(patch["value"]) +","+patch["name"]+"\n"

	with open(buildDirectory+"/patches.csv","w") as f:
		f.write(output)
