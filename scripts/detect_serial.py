import subprocess,sys

if len(sys.argv) != 2:
    print("Usage:",sys.argv[0]," <target>")
    exit(1)
try:
    target = sys.argv[1]
    devices = subprocess.check_output(["ls","-l", "/dev/serial/by-id"], encoding="utf-8").split("\n")
    interfaces = []
    for device in devices:
        device_type = None
        if "usb-SEGGER_J-Link" in device:
            device_type = "zephyr_hci_uart"
        elif "usb-Cypress_WICED_USB__-__Serial_Converter-if00-port0" in device:
            device_type = "cyw20735"

        if device_type is not None:
            interface = "/dev/tty"+device.split("tty")[1]
            interfaces.append((device_type, interface))

    print(",".join([i[1] for i in interfaces if i[0] == target]))
except subprocess.CalledProcessError:
    exit(1)
