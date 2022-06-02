from oasis.interface import openocd, internalblue,nrfutil
from oasis.utils import conf_parser, patch_parser,display
import sys

def patch(target):
    interfaceType = conf_parser.getTargetInterface(target)
    if "INTERNALBLUE" in interfaceType:
        interface = internalblue.InternalblueInterface(target)
    elif "OPENOCD" in interfaceType:
        interface = openocd.OpenocdInterface(target)
    elif "NRFUTIL" in interfaceType:
        interface = nrfutil.NRFUtilInterface(target)

    if not interface.checkSupport("PATCH"):
        print("Interface does not support patching.")
        exit(1)

    patches = patch_parser.getPatches()
    if patches is not None:
        display.start_waiting()
        interface.connect()
        for patch in patches:
            message = "Writing "+patch["patch_name"]+" at "+hex(patch["patch_address"])+" ..."
            if interface.patch(patch["patch_address"], patch["patch_content"]):
                message += "OK"
            else:
                message += "KO"
            display.update_waiting_message(message.replace("\n",""))

        display.update_waiting_message("Applying patches...")
        interface.disconnect()
        display.stop_waiting("\U0001F7E2 Patching process successful !" if interface.isPatchingSuccessful() else "\U0001F534 An error occured during patching.")
    else:
        print("Patch file not found !")

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: "+sys.argv[0]+ " <target>")
        exit(1)

    target = sys.argv[1]
    patch(target)
