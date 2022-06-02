from oasis.controllers.analysis.reverse import disasm,asm
import re,struct,itertools


def findPattern(binaryData, pattern,even=True):
    matches = []
    curpos = 0
    pattern = re.compile(pattern)
    while True:
        m = pattern.search(binaryData[curpos:])
        if m is None:
            break
        if not even or (curpos+m.start()) % 2 == 0:
            matches.append(curpos + m.start())
        curpos += m.end()
    return matches

def generatePattern(instructions,address=0, architecture="thumb"):
    generatedInstructions = []
    for instruction in instructions:
        currentGeneratedInstructions = []
        variables = list(instruction.keys())
        if "instruction" in variables:
            variables.remove("instruction")
        if "joker" in variables:
            variables.remove("joker")
        elif "value" in variables:
            variables.remove("value")
        values = list(itertools.product(*[instruction[variable] for variable in variables]))

        for value in values:
            if "instruction" in instruction:
                instr = instruction["instruction"]
                for variable in variables:
                    instr = instr.replace("<"+variable+">",value[variables.index(variable)])
                currentGeneratedInstructions.append(instr)
            elif "joker" in instruction.keys():
                instr = "<?>" * instruction["joker"]
                currentGeneratedInstructions.append(instr)
            elif "value" in instruction.keys():
                if isinstance(instruction["value"],str):
                    instr = "<val>"+instruction["value"]
                elif isinstance(instruction["value"],bytes):
                    instr = "<val>"+"".join(["{:02x}".format(i) for i in instruction["value"]])

                currentGeneratedInstructions.append(instr)
        generatedInstructions.append(currentGeneratedInstructions)


    currentAddress = address
    output = b""
    for generatedInstruction in generatedInstructions:
        output += b"("
        llen = None
        for instr in generatedInstruction:
            if "<?>" in instr:
                genBytes = instr.replace("<?>",".").encode("ascii")
            elif "<val>" in instr:
                genBytes = bytes.fromhex(instr.replace("<val>","")).replace(b".",b"\.").replace(b"$",b"\$")
            else:
                genBytes = asm(instr,arch=architecture,vma=currentAddress)
            if llen is not None:
                output += b"|"
            output+=genBytes.replace(b"\x00",b"\\x00").replace(b"(",b"\(").replace(b")",b"\)").replace(b"|",b"\|").replace(b"*",b"\*")
            llen = len(genBytes)

        currentAddress += llen if llen is not None else 2
        output += b")"
    return output

def generateAlternatives(*patterns):
    output = b""
    for pattern in patterns:
        output += (b"|" if output != b"" else b"")+b"("+pattern+b")"
    return output


def generateFunctionPointerPattern(address):
    return generatePattern([{"value":struct.pack("I",address+1)}])

def generateValuePattern(value):
    return generatePattern([{"value":struct.pack("I",value)}])
