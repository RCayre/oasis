from string import Template

CONFIGURATION_FILE = """
name:$name
code_start:$code_start
code_size:$code_size
data_start:$data_start
data_size:$data_size
heap_size:$heap_size
rom_start:$rom_start
rom_end:$rom_end
ram_start:$ram_start
ram_end:$ram_end
interface_type:$interface_type
architecture:$architecture
file_type:$file_type
gcc_flags:$gcc_flags
"""

def generateConfiguration(name,code_start,code_size,data_start,data_size,heap_size, memoryMapping,interface_type,architecture, file_type, gcc_flags=""):
    template = Template(CONFIGURATION_FILE)
    return template.substitute(name=name,code_start=hex(code_start),code_size=hex(code_size),data_start=hex(data_start),data_size=hex(data_size),heap_size=hex(heap_size), rom_start=hex(memoryMapping["rom"][0]), rom_end=hex(memoryMapping["rom"][1]),ram_start=hex(memoryMapping["ram"][0]), ram_end=hex(memoryMapping["ram"][1]), interface_type=interface_type,architecture=architecture, file_type=file_type, gcc_flags=gcc_flags)
