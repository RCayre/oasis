import os, os.path

def getTargetPatches(target):
    targetDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../../targets/"+target)
    patches = []
    with open(targetDirectory+"/patch.conf", "r") as f:
        for line in f.readlines():
            line = line.replace("\n","").split(":")
            if len(line) == 6:
                dependency,section,name,address,target,instr = line
                patches.append({"type":"function_hook", "dependency":dependency, "section":section, "name":name, "address":int(address,16), "target_function":target, "instruction":instr})
            elif len(line) == 5:
                dependency,section,name,address,value = line
                if value.startswith("0x"):
                    patches.append({"type":"value", "value":int(value,16), "address":int(address,16),"name":name, "section":section, "dependency":dependency})
                elif value.isdigit():
                    patches.append({"type":"value", "value":int(value), "address":int(address,16),"name":name, "section":section, "dependency":dependency})
                else:
                    patches.append({"type":"function_pointer", "function_pointer":value, "address":int(address,16),"name":name, "section":section, "dependency":dependency})
    return patches

def getPatches():
    try:
        patches = []
        buildDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../../build")
        with open(buildDirectory+"/patches.csv", "r") as f:
            content = [line.replace("\n","").split(",") for line in f.readlines()]
            for patch in content:
                patchType, patchAddress, patchContent, patchName = patch
                patchAddress = int(patchAddress,16)
                patchContent = bytes.fromhex(patchContent)
                patches.append({"patch_type":patchType, "patch_address":patchAddress,"patch_content":patchContent, "patch_name":patchName})
        return patches
    except FileNotFoundError:
        return None

def getMapping(target):
    try:
        patches = []
        mapDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../../maps")
        with open(mapDirectory+"/"+target+".csv", "r") as f:
            content = [line.replace("\n","").split(",") for line in f.readlines()]
            for patch in content:
                patchType, patchAddress, patchContent, patchName = patch
                patchAddress = int(patchAddress,16)
                patchContent = bytes.fromhex(patchContent)
                patches.append({"patch_type":patchType, "patch_address":patchAddress,"patch_content":patchContent, "patch_name":patchName})
        return patches
    except FileNotFoundError:
        return None
