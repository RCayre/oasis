import sys,os

if len(sys.argv) < 3:
	print("Usage: "+sys.argv[0]+" <build dir> <patch file> ")
	exit(1)

buildDir = sys.argv[1]
patchFile = sys.argv[2]
dependencies = ["COMMON"]+sys.argv[3:]

if not os.path.isfile(patchFile):
	print("Patch file does not exist !")
	exit(2)

TEMPLATE = '''
__attribute__((optimize("O0")))
__attribute__((naked))
void %s() {
	__asm__(
	"push {r0-r3,lr}\\n\\t"
	"bl %s\\n\\t"
	"pop {r0-r3}\\n\\t"
	"%s\\n\\t"
	"pop {lr}\\n\\t"
	"bx lr\\n\\t");
}

'''
with open(patchFile,"r") as f:
	output = ""
	for line in f.readlines():
		line = line.replace("\n","").split(":")
		if len(line) == 6:
			tag, section, name, address, target, instr = line
			if tag in dependencies:
				output += TEMPLATE % (name+"_hook",target, instr)
	with open(buildDir+"/hooks.c","w") as fw:
		fw.write(output)
