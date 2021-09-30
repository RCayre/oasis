import sys


if len(sys.argv) == 1:
    print("Usage: "+sys.argv[0]+" <apps>")
    exit(1)

apps = sys.argv[1:]
dependencies = []
for app in apps:
	with open("app/"+app+"/app.conf","r") as f:
		config = {line.replace("\n","").split(":")[0]:line.replace("\n","").split(":")[1] for line in f.readlines()}
		dependencies += config["dependencies"].split(",")
print(" ".join(list(set(dependencies))))
