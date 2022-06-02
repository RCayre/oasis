import sys
from oasis.utils import conf_parser
if len(sys.argv) != 3:
    print("Usage: "+sys.argv[0]+" <target> <info>")
    exit(1)

target = sys.argv[1]
info = sys.argv[2].lower()

if info in ("code_size","code_start","data_size","data_start","name","interface_type","heap_size", "architecture", "file_type","ram_start", "ram_end", "rom_start","rom_end", "gcc_flags", "capabilities"):
    conf = conf_parser.getTargetConfiguration(target)
    value = conf[info]
    if isinstance(value,int):
        print(hex(value))
    else:
        print(value)

elif info == "firmware":
    print(conf_parser.getTargetFirmwareFile(target))

elif info in ("compiler", "assembler", "linker", "objdump", "objcopy", "nm", "architecture_specific_gcc_flags"):
    architecture = conf_parser.getTargetArchitecture(target)
    if info == "compiler":
        print(conf_parser.getCompiler(architecture))
    elif info == "assembler":
        print(conf_parser.getAssembler(architecture))
    elif info == "linker":
        print(conf_parser.getLinker(architecture))
    elif info == "nm":
        print(conf_parser.getNm(architecture))
    elif info == "objcopy":
        print(conf_parser.getObjcopy(architecture))
    elif info == "objdump":
        print(conf_parser.getObjdump(architecture))
    elif info == "architecture_specific_gcc_flags":
        print(conf_parser.getArchitectureSpecificGccFlags(architecture))
