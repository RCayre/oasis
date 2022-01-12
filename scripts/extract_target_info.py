import sys
from utils import conf_parser
if len(sys.argv) != 3:
    print("Usage: "+sys.argv[0]+" <target> <info>")
    exit(1)

target = sys.argv[1]
info = sys.argv[2].lower()

if info in ("code_size","code_start","data_size","data_start","name","interface_type","heap_size", "architecture", "file_type","ram_start", "ram_end", "rom_start","rom_end", "gcc_flags"):
    conf = conf_parser.getConfiguration(target)
    value = conf[info]
    if isinstance(value,int):
        print(hex(value))
    else:
        print(value)

elif info == "firmware":
    print(conf_parser.getTargetFirmwareFile(target))
