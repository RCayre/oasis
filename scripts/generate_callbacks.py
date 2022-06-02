import sys
from oasis.utils import modules

time_callbacks = []
scan_callbacks = []
conn_init_callbacks = []
conn_delete_callbacks = []
conn_rx_callbacks = []
conn_tx_callbacks = []

architecture = sys.argv[1]
modulesList = sys.argv[2:]

for moduleName in modulesList:
    callbacks = modules.getModuleCallbacks(moduleName, architecture=architecture)
    if callbacks is None:
        print("Error: module "+moduleName+" not found.")
    else:
        time_callbacks += callbacks["time_callbacks"]
        scan_callbacks += callbacks["scan_callbacks"]
        conn_init_callbacks += callbacks["conn_init_callbacks"]
        conn_delete_callbacks += callbacks["conn_delete_callbacks"]
        conn_tx_callbacks += callbacks["conn_tx_callbacks"]
        conn_rx_callbacks += callbacks["conn_rx_callbacks"]

modules.generateCallbacksFile(time_callbacks, scan_callbacks,conn_init_callbacks,conn_delete_callbacks, conn_rx_callbacks,conn_tx_callbacks)
