import subprocess

devices = subprocess.check_output(["ls","/dev"],encoding="utf-8").split("\n")
interfaces = []
for device in devices:
	if "ttyUSB" in device:
		interfaces.append(device)
if len(interfaces) > 0:
	print("/dev/"+interfaces[0],end="")
