import sys
from oasis.utils import modules

dependencies = []
modulesList = sys.argv[1:]

for moduleName in modulesList:
    dependencies += modules.getModuleDependencies(moduleName)

print(" ".join(list(set(dependencies))))
