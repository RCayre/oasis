# Testing the target

You can easily check if the target instrumentation code is functional by patching the **monitor_scan**, **monitor_connection** and  **monitor_time** modules.

## Building the embedded software
Let's assume you want to test the cyw20735 IoT Development Kit, which is implemented in *targets/cyw20735*. First, you need to select *cyw20735* as your default target using *oasis* utility:

```bash
$ ./oasis set-target cyw20735

🟢 New default target selected: cyw20735
```

Then, build the embedded software with the modules:

```bash
$ ./oasis build monitor_scan monitor_connection monitor_time

 🔵 Cleaning build files and temporary files...
	rm -rf internalblue*
	rm -rf btsnoop.log
	rm -rf build
 🔵 Creating build directories...
	mkdir -p  build/modules/monitor_scan  build/modules/monitor_connection  build/modules/monitor_time
	mkdir -p build
	mkdir -p maps
 🔵 Building application: monitor_scan
	arm-none-eabi-gcc modules/monitor_scan/module.c -nostdlib -nostartfiles -mthumb -DTIMING_MEASUREMENT -march=armv7-m -ffreestanding -ffunction-sections -fdata-sections -O0   -DSCAN_ENABLED  -DCONNECTION_ENABLED -c -o build/modules/monitor_scan/module.o -I include
 🔵 Building application: monitor_connection
	arm-none-eabi-gcc modules/monitor_connection/module.c -nostdlib -nostartfiles -mthumb -DTIMING_MEASUREMENT -march=armv7-m -ffreestanding -ffunction-sections -fdata-sections -O0   -DSCAN_ENABLED  -DCONNECTION_ENABLED -c -o build/modules/monitor_connection/module.o -I include
 🔵 Building application: monitor_time
	arm-none-eabi-gcc modules/monitor_time/module.c -nostdlib -nostartfiles -mthumb -DTIMING_MEASUREMENT -march=armv7-m -ffreestanding -ffunction-sections -fdata-sections -O0   -DSCAN_ENABLED  -DCONNECTION_ENABLED -c -o build/modules/monitor_time/module.o -I include
 🔵 Generating callbacks...
	python3 scripts/generate_callbacks.py armv7-m monitor_scan monitor_connection monitor_time
 🔵 Generating trampolines snippets...
	python3 scripts/generate_trampolines.py cyw20735 SCAN  CONNECTION
 🔵 Building embedded software...
	arm-none-eabi-gcc  -DSCAN_ENABLED  -DCONNECTION_ENABLED -DHEAP_SIZE=0x800 build/callbacks.c  build/modules/monitor_scan/module.o  build/modules/monitor_connection/module.o  build/modules/monitor_time/module.o src/*.c src/**/*.c build/trampolines.c -nostdlib -nostartfiles -mthumb -DTIMING_MEASUREMENT -march=armv7-m -ffreestanding -ffunction-sections -fdata-sections -O0  targets/cyw20735/wrapper.c -T targets/cyw20735/linker.ld targets/cyw20735/functions.ld -o build/out.elf -I include -Wl,"--defsym=CODE_START=0x271770" -Wl,"--defsym=CODE_SIZE=0x2000" -Wl,"--defsym=DATA_START=0x273770"  -Wl,"--defsym=DATA_SIZE=0x1000"
 🔵 Extracting symbols...
	arm-none-eabi-nm -S -a build/out.elf | sort > build/symbols.sym
 🔵 Generating patches ...
	python3 scripts/generate_patches.py cyw20735 SCAN  CONNECTION
	cp build/patches.csv maps/cyw20735.csv
 🟢 Build process successful !
```
Once generated, the embedded software can be found under *build/patches.csv*.

## Patching the embedded software
Once the embedded software has been generated, you can easily inject it into memory using the **patch** command:

```bash
$ sudo ./oasis patch

Interface connected !
🟢 Patching process successful !
```

## Interact with the test module

First, perform a scan operation using the following command:

```bash
$ sudo ./oasis interact start-scan

Interface connected !
Set Scan Parameters OK
Set Scan Enable OK
```

Then, you can run the following command:
```bash
$ sudo ./oasis interact log

Interface connected !
TIME (timestamp: 60002417, address: 20:73:5b:**:**:**, gap_role: ADVERTISER)
TIME (timestamp: 70814996, address: 20:73:5b:**:**:**, gap_role: ADVERTISER)
SCAN_RX (timestamp: 70827816, valid: 1, channel: 38, rssi: 65455, packet: ******)
SCAN_RX (timestamp: 70828492, valid: 1, channel: 38, rssi: 65456, packet: ******)
SCAN_RX (timestamp: 70830472, valid: 1, channel: 38, rssi: 65454, packet: ******)
SCAN_RX (timestamp: 70836831, valid: 1, channel: 39, rssi: 65457, packet: ******)
SCAN_RX (timestamp: 70837684, valid: 1, channel: 39, rssi: 65457, packet: ******)
SCAN_RX (timestamp: 70839585, valid: 1, channel: 39, rssi: 65452, packet: ******)
[...]
```

If everything works, you should see advertisements packets (SCAN_RX event) in the output and TIME event every second.

You can then stop the scan:
```bash

$ sudo ./oasis interact stop-scan

Interface connected !
Set Scan Enable OK
```

Similarly, you can test the connected mode:
```bash

$ sudo ./oasis interact connect AA:BB:CC:DD:EE:FF random

Interface connected !
```


And by running **log** you should get an output similar to the following one:

```bash
$ sudo ./oasis interact log

Interface connected !
TIME (timestamp: 30081995, address: 20:73:5b:**:**:**, gap_role: SCANNER)
CONN_INIT (access_address: 0x50656a16, crc_init: 0x34377e9, hop_interval: 39, channel_map: 1fffffffff)
CONN_RX (timestamp: 30620327, valid: 1, channel: 17, rssi: 65506, packet: 07090eff7d000000000000)
CONN_RX (timestamp: 30669101, valid: 1, channel: 6, rssi: 65506, packet: 0b060c091d00be02)
CONN_RX (timestamp: 30717850, valid: 1, channel: 25, rssi: 65507, packet: 070914fb0090421b004801)
CONN_RX (timestamp: 30766600, valid: 1, channel: 24, rssi: 65508, packet: 0b0909ff7d000000000000)
CONN_RX (timestamp: 30815350, valid: 1, channel: 33, rssi: 65508, packet: 0500)
CONN_RX (timestamp: 30864029, valid: 1, channel: 16, rssi: 65506, packet: 0b0915fb0090421b004801)
CONN_RX (timestamp: 30912780, valid: 1, channel: 33, rssi: 65508, packet: 0500)
CONN_RX (timestamp: 30961529, valid: 1, channel: 33, rssi: 65508, packet: 0900)
CONN_RX (timestamp: 31010280, valid: 1, channel: 9, rssi: 65506, packet: 0500)
TIME (timestamp: 31109859, address:  20:73:5b:**:**:**, gap_role: CENTRAL)
CONN_RX (timestamp: 31059029, valid: 1, channel: 22, rssi: 65506, packet: 0900)
TIME (timestamp: 31059265, address:  20:73:5b:**:**:**, gap_role: CENTRAL)
CONN_RX (timestamp: 31156530, valid: 1, channel: 17, rssi: 65506, packet: 0500)
CONN_RX (timestamp: 31205279, valid: 1, channel: 25, rssi: 65509, packet: 0900)
CONN_RX (timestamp: 31254029, valid: 1, channel: 21, rssi: 65506, packet: 0500)
[...]
```
