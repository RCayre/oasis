import sys
from oasis.utils import builder,patch_parser,conf_parser

if len(sys.argv) == 1:
    print("Usage: "+sys.argv[0]+" <target> <dependencies>")
    exit(1)

target = sys.argv[1]
dependencies = ["COMMON"] + sys.argv[2:]

patches = patch_parser.getTargetPatches(target)
builder.generateTrampolineFile(patches,dependencies, conf_parser.getTargetArchitecture(target))
