import controllers
import sys,os,os.path

if len(sys.argv) < 4:
    print("Usage: "+sys.argv[0]+" <firmware> <controller_type> <target_name> [--interface-type=INTERNALBLUE_ADB|INTERNALBLUE_ADB_SERIAL|INTERNALBLUE_HCI|NRF51_JLINK_OPENOCD|NRF51_STLINK_OPENOCD --code-size=CODE_SIZE --data-size=DATA_SIZE --code-start=CODE_START --data-start=DATA_START --heap-size --find-memory-zone=PATCHRAM|BLOC|AUTO --no-generation]")
    sys.exit(1)

controllerName = sys.argv[2].upper()
if controllerName == "BROADCOM":
    controller = controllers.BroadcomController(sys.argv[1])
elif controllerName == "NRF51_SOFTDEVICE":
    controller = controllers.NRF51SoftDeviceController(sys.argv[1])
#elif controllerName == "NRF52_SOFTDEVICE":
#    controller = controllers.NRF52SoftDeviceController(sys.argv[1])
else:
    controller = None

name = sys.argv[3]

interfaceType = None
codeSize = None
codeStart = None
dataSize = None
dataStart = None
heapSize = None
findMemoryZone = None
noGeneration = False

for parameter in sys.argv[4:]:
    if "--no-generation" in parameter:
        noGeneration = True
    if "--interface-type=" in parameter:
        interfaceType = parameter.split("=")[1].upper()
    elif "--code-size=" in parameter:
        if "0x" in parameter.split("=")[1]:
            codeSize = int(parameter.split("=")[1],16)
        else:
            codeSize = int(parameter.split("=")[1])
    elif "--data-size=" in parameter:
        if "0x" in parameter.split("=")[1]:
            dataSize = int(parameter.split("=")[1],16)
        else:
            dataSize = int(parameter.split("=")[1])
    elif "--code-start=" in parameter:
        if "0x" in parameter.split("=")[1]:
            codeStart = int(parameter.split("=")[1],16)
        else:
            codeStart = int(parameter.split("=")[1])
    elif "--heap-size=" in parameter:
        if "0x" in parameter.split("=")[1]:
            heapSize = int(parameter.split("=")[1],16)
        else:
            heapSize = int(parameter.split("=")[1])

    elif "--data-start=" in parameter:
        if "0x" in parameter.split("=")[1]:
            dataStart = int(parameter.split("=")[1],16)
        else:
            dataStart = int(parameter.split("=")[1])
    elif "--find-memory-zone=" in parameter:
        findMemoryZone = parameter.split("=")[1].upper()

if interfaceType is None:
    interfaceType = "NRF51_JLINK_OPENOCD" if controllerName != "BROADCOM" else "INTERNALBLUE_HCI"
if codeSize is None:
    codeSize = 0x1500
if dataSize is None:
    dataSize = 0x2000
if heapSize is None:
    heapSize = int(dataSize/2)
if findMemoryZone is None:
    findMemoryZone = "AUTO" if controllerName != "BROADCOM" else "PATCHRAM"


controller.setParameters(name, interfaceType, codeSize,codeStart,dataSize,dataStart,heapSize, findMemoryZone)
if controller is not None:
    controller.extractFirmwareStructure()
    controller.extractFirmwareInformations()

    controller.extractFunctions()
    controller.extractDatas()

    controller.showFunctions()
    print("-"*40)
    controller.showDatas()
    print("-"*40)
    if not noGeneration:
        controller.generateTarget()
