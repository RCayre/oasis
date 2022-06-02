import os, os.path
import shutil

def generateTarget(firmwarePath, fileType,  name, configuration, wrapper, mainLinkerScript, functionsLinkerScript,patches):
    targetDirectory =  os.path.abspath(os.path.dirname(__file__)+"/../../../targets/"+name)
    if not os.path.exists(targetDirectory):
        os.mkdir(targetDirectory)
        shutil.copyfile(firmwarePath,targetDirectory+"/firmware."+fileType)
        with open(targetDirectory+"/target.conf","w") as f:
            f.write(configuration)
        with open(targetDirectory+"/patch.conf","w") as f:
            f.write(patches)
        with open(targetDirectory+"/wrapper.c","w") as f:
            f.write(wrapper)
        with open(targetDirectory+"/linker.ld","w") as f:
            f.write(mainLinkerScript)
        with open(targetDirectory+"/functions.ld","w") as f:
            f.write(functionsLinkerScript)
        return True
    return False
