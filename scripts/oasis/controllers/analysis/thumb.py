from oasis.controllers.analysis.reverse import disasm,asm
from oasis.utils import exec
import struct

def assemble(binaryData, offset=0):
    return asm(binaryData, arch="thumb", vma=offset)

def disassemble(binaryData,offset=0):
    instructions = []
    for instruction in disasm(binaryData,arch="thumb",vma=offset).split("\n"):
        if instruction != "":
            try:
                address = int(instruction.split()[0].replace(":",""),16)
                if address == len(instructions):
                    instructions.append(instruction)
                else:
                    while len(instructions) != address:
                        instructions.append(None)
                    instructions.append(instruction)

            except ValueError:
                pass
    return instructions

def exploreInstructions(instructions):
    for instruction in instructions:
        if instruction is not None:
            yield instruction

def extractInstructionAddress(instruction):
    return int(instruction.split()[0].replace(":",""),16)


def extractTargetAddressFromJump(instruction):
    return int(instruction.split()[-2],16)


def extractTargetAddressFromLoadOrStore(instruction):
    return int(instruction.split()[-2].replace("(",""),16)

def extractOffsetFromLoadOrStore(instruction):
    offset = instruction.split()[-1].replace("]","").replace("#","")
    if "0x" in offset:
        return int(offset,16)
    else:
        return int(offset)

def extractBaseRegisterFromLoadOrStore(instruction):
    return instruction.split()[-2].replace("[","").replace(",","")

def extractFirstRegisterFromAdds(instruction):
    return instruction.split()[-3].replace(",","")

def extractSecondRegisterFromAdds(instruction):
    return instruction.split()[-2].replace(",","")

def extractDestRegisterFromLoadOrStore(instruction):
    return instruction.split()[3].replace(",","")

def extractDestRegisterFromBic(instruction):
    return instruction.split()[4].replace(",","")

def extractOffsetFromAddOrSub(instruction):
    return int(instruction.split()[-1].replace("#",""))

def extractValue(pointer):
    return struct.unpack("I", pointer)[0]

def extractAddressFromFunctionPointer(pointer):
    return struct.unpack("I", pointer)[0] - 1

def extractTextFromInstruction(instruction):
    text = instruction.split("       ")[2]
    if ";" in text:
        text = text.split(";")[0]
    if "<" in text:
        text = text.split("<")[0]
        text = text.split()[0]+" "+"0x"+text.split()[1]
    return text

def findReferences(instructions,address):
    references = []
    for instruction in exploreInstructions(instructions):
        if "blx" in instruction:
            pass
        elif "bl " in instruction or " b." in instruction:
            destination = int(instruction.split()[-2],16)
            if address == destination:
                references.append(extractInstructionAddress(instruction))
    return references
