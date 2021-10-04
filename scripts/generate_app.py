from pwnlib.asm import asm
import sys, os, subprocess
import re

if len(sys.argv) == 1:
    print("Usage: "+sys.argv[0]+" <builddir> <apps>")
    exit(1)

if len(sys.argv) == 2:
    exit(0)

builddir = sys.argv[1]
apps = sys.argv[2:]

# Recover symbol name
scan_callbacks = []
conn_rx_callbacks = []
conn_tx_callbacks = []
for app in apps:
    symbols = subprocess.check_output(["arm-none-eabi-nm", builddir + "/app/" + app + "/app.o"], encoding="utf-8")
    symbols = symbols.split("\n")
    for symbol in symbols:
        if " T " in symbol:
            name = symbol.split(" ")[2]
            if "_scan_callback_" in name:
                scan_callbacks += [name]
            elif "_conn_rx_callback_" in name:
                conn_rx_callbacks += [name]
            elif "_conn_tx_callback_" in name:
                conn_tx_callbacks += [name]

# Generate app.c
content = ""

content += '#include "types.h"\n'
content += '#include "metrics.h"\n'
content += "\n"

# Callback prototype
for callback in scan_callbacks + conn_rx_callbacks + conn_tx_callbacks:
    content += "void " + callback + "(metrics_t * metrics);\n"

# Number of callbacks for scan
content += "uint8_t scan_callbacks_size = " + str(len(scan_callbacks)) + ";\n"
# Callbacks
content += "callback_t scan_callbacks[" + str(len(scan_callbacks)) + "] = {\n"
for callback in scan_callbacks:
    content += "\t" + callback + ",\n"
content += "};\n\n"

# Number of callbacks for RX conn
content += "uint8_t conn_rx_callbacks_size = " + str(len(conn_rx_callbacks)) + ";\n"
# Callbacks
content += "callback_t conn_rx_callbacks[" + str(len(conn_rx_callbacks)) + "] = {\n"
for callback in conn_rx_callbacks:
    content += "\t" + callback + ",\n"
content += "};\n\n"

# Number of callbacks for TX conn
content += "uint8_t conn_tx_callbacks_size = " + str(len(conn_tx_callbacks)) + ";\n"
# Callbacks
content += "callback_t conn_tx_callbacks[" + str(len(conn_tx_callbacks)) + "] = {\n"
for callback in conn_tx_callbacks:
    content += "\t" + callback + ",\n"
content += "};\n\n"

# Write to app.c
with open(builddir + "/" + "app.c", "w") as f:
    f.write(content)
