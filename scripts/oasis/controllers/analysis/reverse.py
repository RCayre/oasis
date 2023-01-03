import re,tempfile,shutil
from oasis.utils import exec
from oasis.controllers.analysis.exceptions import AssemblyFailure,DisassemblyFailure
# Note: these functions are intented to be use as a replacement for pwnlib dependencies (to fix some versions-related issues)
# This code is greatly inspired by pwntools project, especially pwnlib/asm.py : https://github.com/Gallopsled/pwntools

THUMB_HEADER = '''
.section .shellcode,"ax"
.global _start
.global __start
_start:
__start:
.syntax unified
.arch armv7-a
.thumb
'''

ARM_HEADER = '''
.section .shellcode,"ax"
.global _start
.global __start
_start:
__start:
.syntax unified
.arch armv7-a
.arm
'''

asm_headers = {
    "thumb":THUMB_HEADER,
    "arm":ARM_HEADER
}

asm_architectures = {
    "arm":"arm",
    "thumb":"arm"
}

asm_targets = {
    "arm":{"little":"elf32-littlearm", "big":"elf32-bigarm"},
    "thumb":{"little":"elf32-littlearm", "big":"elf32-bigarm"},
}

asm_tools = {
    "arm":{"objcopy":"arm-none-eabi-objcopy", "objdump":"arm-none-eabi-objdump", "as":"arm-none-eabi-as", "ld":"arm-none-eabi-ld"},
    "thumb":{"objcopy":"arm-none-eabi-objcopy", "objdump":"arm-none-eabi-objdump", "as":"arm-none-eabi-as", "ld":"arm-none-eabi-ld"},
}

asm_as_flags = {
    "arm":[],
    "thumb":["-mthumb"]
}

def disasm(data, vma=0, arch="thumb", endianness="little"):
    temporaryDirectory = tempfile.mkdtemp(prefix = 'oasis-disassembler-')
    rawFile = temporaryDirectory+"/raw"
    elfFile = temporaryDirectory+"/elf"

    with open(rawFile, "wb") as f:
        f.write(data)

    objcopy = [asm_tools[arch]["objcopy"],'-I', 'binary', '-O', asm_targets[arch][endianness], '-B', asm_architectures[arch], '--set-section-flags', '.data=code', '--rename-section', '.data=.text']
    if arch == 'thumb':
        objcopy += ["--prefix-symbol=$t."]
    else:
        objcopy += ["-w", "-N", "*"]

    out,err = exec.execute_with_output(objcopy+[rawFile,elfFile])
    if len(err) > 0:
        raise DisassemblyFailure


    objdump = [asm_tools[arch]["objdump"], '-d', '--adjust-vma', hex(vma), '-b', asm_targets[arch][endianness]]
    out,err = exec.execute_with_output(objdump+[elfFile])
    if len(err) > 0:
        raise DisassemblyFailure

    shutil.rmtree(temporaryDirectory)

    out = out.decode()
    out2 = out.split('<.text>:\n')

    if len(out2) != 2:
        raise DisassemblyFailure

    result = out2[1].strip('\n').rstrip().expandtabs()


    lines = []
    pattern = '^( *[0-9a-f]+: *)', '((?:[0-9a-f]+ )+ *)', '(.*)'
    pattern = ''.join(pattern)
    for line in result.splitlines():
        match = re.search(pattern, line)
        if not match:
            lines.append(line)
            continue

        groups = match.groups()

        o, b, i = groups
        line = ''
        line += o + b + i
        lines.append(line)

    return re.sub(',([^ ])', r', \1', '\n'.join(lines))


def asm(instructions,vma=0, arch="thumb", endianness="little"):
    temporaryDirectory = tempfile.mkdtemp(prefix = 'oasis-assembler-')
    asmFile = temporaryDirectory+"/asm"
    assembledFile = temporaryDirectory+"/assembled"
    linkedFile = temporaryDirectory+"/linked"
    rawFile = temporaryDirectory+"/raw"

    code = asm_headers[arch] + instructions

    with open(asmFile,"w") as f:
        f.write(code)

    endiannessFlag = ["-EL"] if endianness == "little" else ["-EB"]
    ast = [asm_tools[arch]["as"]] + asm_as_flags[arch] + endiannessFlag + ["-o"]
    out,err = exec.execute_with_output(ast+[assembledFile,asmFile])


    ld_start = [asm_tools[arch]["ld"],"-z","execstack","-o"]
    ld_end = ['--section-start=.shellcode='+hex(vma), '--entry='+hex(vma), '-shared','-init=_start', '-z', 'max-page-size=4096','-z','common-page-size=4096']
    out,err = exec.execute_with_output(ld_start+[linkedFile,assembledFile]+ld_end)
    if len(err) > 0:
        raise AssemblyFailure

    objcopy = [asm_tools[arch]["objcopy"], "-j", ".shellcode", "-Obinary"]
    out,err = exec.execute_with_output(objcopy+[linkedFile,rawFile])
    if len(err) > 0:
        raise AssemblyFailure

    with open(rawFile,"rb") as f:
        result = f.read()
    shutil.rmtree(temporaryDirectory)
    return result
