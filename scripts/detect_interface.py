import subprocess

devices = subprocess.check_output(["ls","/dev"],encoding="utf-8").split("\n")
interfaces = []
for device in devices:
    if "ttyUSB" in device:
        interfaces.append(device)

if len(interfaces) > 0:
    order = sorted([int(i.split("ttyUSB")[1]) for i in interfaces])
    print("/dev/ttyUSB"+str(order[0]),end="")
