import os, os.path
from oasis.utils import conf_default

def setDefaultTarget(target):
    rootDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../..")
    try:
        with open(rootDirectory+"/oasis.conf", "r") as f:
            content = f.read()
        newContent = ""
        found = False
        for line in content.split("\n"):
            if line != "":
                key,value = line.split(":")
                if key == "default_target":
                    value = target
                    found = True
                newContent += key+":"+value+"\n"
        if not found:
            newContent += "default_target:"+target+"\n"
        with open(rootDirectory+"/oasis.conf", "w") as f:
            f.write(newContent)
    except FileNotFoundError:
        with open(rootDirectory+"/oasis.conf", "w") as f:
            f.write("default_target:"+target+"\n")

def getMainConfiguration():
    rootDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../..")
    configuration = conf_default.default_configuration
    try:
        with open(rootDirectory+"/oasis.conf", "r") as f:
            content = f.read()
        for line in content.split("\n"):
            if line != "":
                key,value = line.split(":")
                configuration[key] = value
    except FileNotFoundError:
        configuration = conf_default.default_configuration
    return configuration

def getCompiler(architecture):
    if "arm" in architecture or "thumb" in architecture:
        return getMainConfiguration()["arm_gcc"]

def getLinker(architecture):
    if "arm" in architecture or "thumb" in architecture:
        return getMainConfiguration()["arm_ld"]

def getAssembler(architecture):
    if "arm" in architecture or "thumb" in architecture:
        return getMainConfiguration()["arm_as"]

def getObjcopy(architecture):
    if "arm" in architecture or "thumb" in architecture:
        return getMainConfiguration()["arm_objcopy"]

def getObjdump(architecture):
    if "arm" in architecture or "thumb" in architecture:
        return getMainConfiguration()["arm_objdump"]

def getNm(architecture):
    if "arm" in architecture or "thumb" in architecture:
        return getMainConfiguration()["arm_nm"]

def getArchitectureSpecificGccFlags(architecture):
    if "arm" in architecture or "thumb" in architecture:
        return getMainConfiguration()["arm_gcc_flags"]

def getOpenocd():
    return getMainConfiguration()["openocd"]

def getPython():
    return getMainConfiguration()["python3"]

def getNrfutil():
    return getMainConfiguration()["nrfutil"]

def getDefaultTarget():
    return getMainConfiguration()["default_target"]

def getTargets():
    targetDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../../targets/")
    return os.listdir(targetDirectory)

def getTargetConfiguration(target):
    targetDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../../targets/"+target)
    configuration = {}
    with open(targetDirectory+"/target.conf", "r") as f:
        content = f.read()
    for line in content.split("\n"):
        if line != "":
            key,value = line.split(":")
            if "_start" in key or "_size" in key or "_end" in key:
                if value.startswith("0x"):
                    value = int(value,16)
                else:
                    value = int(value)
            configuration[key] = value
    return configuration

def getTargetName(target):
    return getTargetConfiguration(target)["name"]

def getTargetCapabilities(target):
    return getTargetConfiguration(target)["capabilities"].split(",")

def getTargetInterface(target):
    return getTargetConfiguration(target)["interface_type"]

def getTargetCodeZone(target):
    conf = getTargetConfiguration(target)
    return (conf["code_start"],conf["code_size"])

def getTargetDataZone(target):
    conf = getTargetConfiguration(target)
    return (conf["data_start"],conf["data_size"])

def getTargetHeapSize(target):
    return getTargetConfiguration(target)["heap_size"]

def getTargetRom(target):
    conf = getTargetConfiguration(target)
    return (conf["rom_start"],conf["rom_end"])

def getTargetRam(target):
    conf = getTargetConfiguration(target)
    return (conf["ram_start"],conf["ram_end"])

def getTargetFirmwareType(target):
    return getTargetConfiguration(target)["file_type"]

def getTargetArchitecture(target):
    return getTargetConfiguration(target)["architecture"]

def getTargetGCCFlags(target):
    return getTargetConfiguration(target)["gcc_flags"]

def getTargetFirmwareFile(target):
    targetDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../../targets/"+target)
    return targetDirectory+"/firmware."+getTargetFirmwareType(target)
