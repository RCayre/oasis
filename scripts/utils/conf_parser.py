import os, os.path

def getConfiguration(target):
    targetDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../targets/"+target)
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
    return getConfiguration(target)["name"]

def getTargetInterface(target):
    return getConfiguration(target)["interface_type"]

def getTargetCodeZone(target):
    conf = getConfiguration(target)
    return (conf["code_start"],conf["code_size"])

def getTargetDataZone(target):
    conf = getConfiguration(target)
    return (conf["data_start"],conf["data_size"])

def getTargetHeapSize(target):
    return getConfiguration(target)["heap_size"]

def getTargetRom(target):
    conf = getConfiguration(target)
    return (conf["rom_start"],conf["rom_end"])

def getTargetRam(target):
    conf = getConfiguration(target)
    return (conf["ram_start"],conf["ram_end"])

def getTargetFirmwareType(target):
    return getConfiguration(target)["file_type"]

def getTargetArchitecture(target):
    return getConfiguration(target)["architecture"]

def getTargetGCCFlags(target):
    return getConfiguration(target)["gcc_flags"]

def getTargetFirmwareFile(target):
    targetDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../targets/"+target)
    return targetDirectory+"/firmware."+getTargetFirmwareType(target)
