import sys
from utils import builder

if len(sys.argv) == 1:
    print("Usage: "+sys.argv[0]+" <target> <dependencies>")
    exit(1)

target = sys.argv[1]
dependencies = ["COMMON"] + sys.argv[2:]

builder.generatePatchesFile(target,dependencies)
