LINKER_FILE = """
MEMORY
{
    code (rwx) : ORIGIN = CODE_START, LENGTH = CODE_SIZE
    data (rwx) : ORIGIN = DATA_START, LENGTH = DATA_SIZE
}


SECTIONS {
    .text : {
    } > code

    .rodata : {
    } > code

    .bss : {
    } > data

    .data : {
    } > data

    .bss.memory : {
    } > data
}

"""

def generateFunction(name, address):
    return name + " = "+hex(address)+";"

def generateFunctions(functions):
    out = ""
    for k,v in functions.items():
        out += generateFunction(k,v)+"\n"
    return out

def generateMemoryZonesAndSections():
    return LINKER_FILE
