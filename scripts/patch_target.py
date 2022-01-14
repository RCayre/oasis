from interface import openocd, internalblue
from utils import conf_parser, patch_parser,display
import sys

if len(sys.argv) != 2:
    print("Usage: "+sys.argv[0]+ " <target>")
    exit(1)

target = sys.argv[1]

interfaceType = conf_parser.getTargetInterface(target)
if "INTERNALBLUE" in interfaceType:
    interface = internalblue.InternalblueInterface(target)
else:
    interface = openocd.OpenocdInterface(target)

patches = patch_parser.getPatches()
if patches is not None:
    interface.connect()
    count = 1
    error = False
    for patch in patches:
        message = "Writing "+patch["patch_name"]+" at "+hex(patch["patch_address"])+" ..."
        if interface.patch(patch["patch_address"], patch["patch_content"]):
            message += "OK"
        else:
            message += "KO"
            error = True
        display.progress(count, len(patches),message.replace("\n",""))
        count += 1
        sys.stdout.flush()
    print()
    interface.disconnect()

else:
    print("Patch file not found !")
