import os,os.path
from string import Template
from utils import exec,builder

MODULE_CONFIGURATION = """
name:$name
description:$description
dependencies:$dependencies
"""

def generateEmptyModule(name, description, dependencies):
    moduleDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../modules/"+name)
    if not os.path.exists(moduleDirectory):
        template = Template(MODULE_CONFIGURATION)
        configurationFile = template.substitute(name=name, description=description, dependencies=dependencies)
        with open(moduleDirectory+"/module.conf", "w") as f:
            f.write(configurationFile)
        with open(moduleDirectory+"/module.c","w") as f:
            f.write("")
        return True
    return False

def getModuleDependencies(name):
    moduleDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../modules/"+name)
    dependencies = []
    try:
        with open(moduleDirectory+"/module.conf","r") as f:
            config = {line.replace("\n","").split(":")[0]:line.replace("\n","").split(":")[1] for line in f.readlines()}
            dependencies = config["dependencies"].split(",")
        return dependencies
    except:
        return []

def getModuleCallbacks(name):
    time_callbacks = []
    scan_callbacks = []
    conn_init_callbacks = []
    conn_delete_callbacks = []
    conn_rx_callbacks = []
    conn_tx_callbacks = []
    moduleBuildDirectory = os.path.abspath(os.path.dirname(__file__)+"/../../build/modules/"+name)
    if os.path.exists(moduleBuildDirectory):
        for symbol in exec.execute(["arm-none-eabi-nm", moduleBuildDirectory+"/module.o"]):
            if " T " in symbol:
                name = symbol.split(" ")[2].replace("\n","")
                if "_time_callback_" in name:
                    time_callbacks += [name]
                elif "_scan_callback_" in name:
                    scan_callbacks += [name]
                elif "_conn_rx_callback_" in name:
                    conn_rx_callbacks += [name]
                elif "_conn_init_callback_" in name:
                    conn_init_callbacks += [name]
                elif "_conn_delete_callback_" in name:
                    conn_delete_callbacks += [name]
                elif "_conn_tx_callback_" in name:
                    conn_tx_callbacks += [name]
        return {"time_callbacks":time_callbacks, "scan_callbacks":scan_callbacks,"conn_init_callbacks":conn_init_callbacks,"conn_delete_callbacks":conn_delete_callbacks,  "conn_rx_callbacks":conn_rx_callbacks, "conn_tx_callbacks":conn_tx_callbacks}
    else:
        return None

def generateCallbacksFile(time_callbacks, scan_callbacks,conn_init_callbacks,conn_delete_callbacks,  conn_rx_callbacks, conn_tx_callbacks):
    content = '#include "types.h"\n'
    content += '#include "metrics.h"\n'
    content += "\n"

    # Callback prototype
    for callback in time_callbacks + scan_callbacks + conn_init_callbacks + conn_delete_callbacks  + conn_rx_callbacks + conn_tx_callbacks:
        content += "void " + callback + "(metrics_t * metrics);\n"

    content += "\n\n"
    # Number of callbacks for scan
    content += "uint8_t time_callbacks_size = " + str(len(time_callbacks)) + ";\n"
    # Callbacks
    content += "callback_t time_callbacks[" + str(len(time_callbacks)) + "] = {\n"
    for callback in time_callbacks:
        content += "\t" + callback + ",\n"
    content += "};\n\n"

    # Number of callbacks for scan
    content += "#ifdef SCAN_ENABLED\n\n"
    content += "uint8_t scan_callbacks_size = " + str(len(scan_callbacks)) + ";\n"
    # Callbacks
    content += "callback_t scan_callbacks[" + str(len(scan_callbacks)) + "] = {\n"
    for callback in scan_callbacks:
        content += "\t" + callback + ",\n"
    content += "};\n\n"
    content += "#endif\n\n"

    # Number of callbacks for RX conn
    content += "#ifdef CONNECTION_ENABLED\n\n"
    content += "uint8_t conn_init_callbacks_size = " + str(len(conn_init_callbacks)) + ";\n"
    # Callbacks
    content += "callback_t conn_init_callbacks[" + str(len(conn_init_callbacks)) + "] = {\n"
    for callback in conn_init_callbacks:
        content += "\t" + callback + ",\n"
    content += "};\n\n"

    content += "uint8_t conn_delete_callbacks_size = " + str(len(conn_delete_callbacks)) + ";\n"
    # Callbacks
    content += "callback_t conn_delete_callbacks[" + str(len(conn_delete_callbacks)) + "] = {\n"
    for callback in conn_delete_callbacks:
        content += "\t" + callback + ",\n"
    content += "};\n\n"

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
    content += "#endif\n\n"

    with open(builder.getBuildDirectory()+"/callbacks.c", "w") as f:
        f.write(content)
