# Adding a custom target

A *Target* includes a set of files allowing the embedded software to interact with the native controller firmware. It includes the following files:

* *firmware.bin* : targeted controller firmware
* *functions.ld* : memory mapping of used functions in controller firmare
* *linker.ld* : linker configuration file
* *patch.conf* : list of patches needed to instrument the controller firmware
* *target.conf* : target configuration file
* *wrapper.c*  : wrapper source code


## Supported targets
Currently, the framework supports the following targets, listed in **targets/** directory:

| Target name                | Corresponding device                 | Chip | Firmware |
|----------------------------|:------------------------------------:|-----:|---------:|
| cyw20735                   | BLE/BR Bluetooth 5.0 Evaluation Kit CYW920735Q60EVB-01 |CYW20735 (Cypress) | Native firmware (Jan 18 2018) |
| nexus5                     | Nexus 5 Smartphone                   |BCM4335C0 | Native firmware (Dec 11 2012) |
| raspi3                     | Raspberry Pi 3B+                   |BCM4345C0 | Native firmware (Aug 19 2014) |
| gablys                     | Gablys Smart Keyfob                  |nRF51822 | OpenLys firmware |
| nrf51_blinky               | Nordic SemiConductors nRF51 Development Kit (pca10028)|nRF51422 | Nordic SemiConductors SDK example (ble_app_multilink_central) |
| nrf51_advertiser           | Nordic SemiConductors nRF51 Development Kit (pca10028)|nRF51422 | Nordic SemiConductors SDK example (ble_app_beacon) |
| nrf51_peripheral           | Nordic SemiConductors nRF51 Development Kit (pca10028)|nRF51422 | Nordic SemiConductors SDK example (ble_app_blinky) |
| nrf51_scanner              | Nordic SemiConductors nRF51 Development Kit (pca10028) |nRF51422 | Nordic SemiConductors SDK example (ble_app_uart_c) |
| zephyr_hci_dongle          | Nordic SemiConductors nRF52 Dongle (pca10059)|nRF52840 | Zephyr HCI USB example |
| zephyr_hci_uart            | Nordic SemiConductors nRF52 Development Kit (pca10040) |nrf52840 | Zephyr HCI UART example |
| zephyr_scanner             | Nordic SemiConductors nRF52 Development Kit (pca10040) |nrf52840 | Zephyr Scanner example |
| zephyr_peripheral          | Nordic SemiConductors nRF52 Development Kit (pca10040) |nrf52840 | Zephyr Peripheral example |


## Broadcom and Cypress chips

If your target is not included in the previous list, but is based on a Broadcom / Cypress chip, you can use the *Firmware Analyzer* to generate automatically the target files:

* Dump the firmware of your target (it should be compatible with InternalBlue)
* Execute the *Firmware Analyzer* using the following command:

```
python3 scripts/generate_target.py <firmware file> BROADCOM <target name> --interface-type=<interface type>
```

With:

* *<firmware file>* the firmware binary file
* *<target name>* the name of the target
* *<interface type>* a string indicating the backend interface to use to communicate with the target: "INTERNALBLUE_ADB", "INTERNALBLUE_ADB_SERIAL" or "INTERNALBLUE_HCI"

You can also use an automatic heuristic to discover a memory zone to use in order to inject the code and data into the memory with **--find-memory-zone=PATCHRAM|BLOC** parameter.

* **PATCHRAM** will try to find a free memory zone at the end of the PatchRAM section, used by the manufacturer to update the firmware code
* **BLOC** will use a unused BLOC buffer to find a free memory zone into RAM

For example:

```
python3 scripts/generate_target.py firmware.bin BROADCOM my_new_target --interface-type=INTERNALBLUE_ADB --find-memory-zone=PATCHRAM
```

If these strategies fail, you can provide a memory zone manually using **--data-start**, **--data-size**, **--code-start** and **--code-size** parameters:

```
python3 scripts/generate_target.py firmware.bin BROADCOM my_new_target --interface-type=INTERNALBLUE_ADB --code-start=0x271770 --code-size=0x2000 --data-start=0x273770 --data-size=0x1000
```

Once generated, a new target directory and the corresponding files have been added to **targets** directory.


## nRF51 chips (SoftDevice)

If your target is not included in this list, but is based on a Nordic SemiConductors nRF51 chip and uses the SoftDevice proprietary stack from Nordic, you can automatically generate the target files using:

 ```
 python3 scripts/generate_target.py <firmware file> NRF51_SOFTDEVICE <target name> --interface-type=<interface type>
 ```

 With:

 * *<firmware file>* the firmware hex file
 * *<target name>* the name of the target
 * *<interface type>* a string indicating the backend interface to use to communicate with the target: "NRF51_JLINK_OPENOCD" or "NRF51_STLINK_OPENOCD"

For example:

 ```
 python3 scripts/generate_target.py firmware.hex NRF51_SOFTDEVICE my_new_target2 --interface-type=NRF51_STLINK_OPENOCD
 ```

You can automatically identify a free memory zone to store the code and the data of the embedded software using **--find-memory-zone=AUTO** parameter, or provide it manually using  **--data-start**, **--data-size**, **--code-start** and **--code-size** parameters:

 ```
 python3 scripts/generate_target.py firmware.hex NRF51_SOFTDEVICE my_new_target2 --interface-type=NRF51_STLINK_OPENOCD --code-start=0x271770 --code-size=0x2000 --data-start=0x273770 --data-size=0x1000
 ```

Once generated, a new target directory and the corresponding files have been added to **targets** directory.


## nRF52 chips (Zephyr)

If your target is not included in this list, but is based on a Nordic SemiConductors nRF52 chip and uses the Zephyr BLE stack, you can automatically generate the target files using:

```
python3 scripts/generate_target.py <firmware file> NRF52_ZEPHYR <target name> --interface-type=<interface type>
```

 With:

 * *<firmware file>* the firmware hex file
 * *<target name>* the name of the target
 * *<interface type>* a string indicating the backend interface to use to communicate with the target: "NRF52_JLINK_OPENOCD" or "NRF52_NRFUTIL"

For example:

```
python3 scripts/generate_target.py firmware.hex NRF52_ZEPHYR my_new_target3 --interface-type=NRF52_JLINK_OPENOCD
```

You can automatically identify a free memory zone to store the code and the data of the embedded software using **--find-memory-zone=AUTO** parameter, or provide it manually using  **--data-start**, **--data-size**, **--code-start** and **--code-size** parameters:

```
python3 scripts/generate_target.py firmware.hex NRF52_ZEPHYR my_new_target3 --interface-type=NRF52_JLINK_OPENOCD --code-start=0x271770 --code-size=0x2000 --data-start=0x273770 --data-size=0x1000
```

Once generated, a new target directory and the corresponding files have been added to **targets** directory.

## Writing a custom target

If your target is not covered in the previous sections, you can manually create a new target by creating a new directory indicating your target name in the **targets** directory:

```
mkdir targets/new_target
```

Copy your target's firmware into the directory as *firmware.hex* or *firmware.bin*:

```
cp ~/path/to/my/firmware.hex targets/firmware.hex
```

Then, you have to add several configuration, linker and source code files describing how to instrument the target, described in the next sections.
Let us note that the framework provides a basic dependency mechanism, allowing to only include the necessary components depending on the selected modules requirements. Three dependencies are supported:

* **COMMON**: everything linked to this dependency will be systematically included
* **SCAN**: everything linked to this dependency will be included if one of the selected module needs scanning capabilities
* **CONNECTION**: everything linked to this dependency will be included if one of the selected module needs connection capabilities

### Linker files

* *functions.ld* lists the native functions that need to be available from the embedded software and the corresponding address in memory. The following example shows the functions used by the *cyw20735* target:

```
utils_memcpy8 = 0xadbe4;
__rt_memcpy = 0x688be;
btclk_GetNatClk_clkpclk = 0x9bc30;
btclk_Convert_clkpclk_us = 0x9bbd2;
lm_getRawRssiWithTaskId = 0xae6a2;
bthci_event_AllocateEventAndFillHeader = 0x24e92;
bthci_event_AttemptToEnqueueEventToTransport = 0x24c36;
```

* *linker.ld* contains the linker script, indicating the memory zones to use to store the data and the code. You can use the following template to automatically use the values indicated in *target.conf*:

```
MEMORY
{
    code (rwx) : ORIGIN = CODE_START, LENGTH = CODE_SIZE
    data (rwx) : ORIGIN = DATA_START, LENGTH = DATA_SIZE
}


SECTIONS {
    .text : {
    } > code

    .rodata : {
    } > code

    .bss : {
    } > data

    .data : {
    } > data

    .bss.memory : {
    } > data
}
```

### Wrapper and patches

* *wrapper.c* contains the C source code allowing to instrument the target. It implements the following low level functions, mainly used by the *Core*:

| Function name              | Prototype      | Description |
|----------------------------|:---------------|:-----------:|
**memcpy** | `void * memcpy(void * dst, void * src, uint32_t size)` | standard copy function |
**get_timestamp_in_us** | `uint32_t get_timestamp_in_us()` | returns the timestamp of last received packet (in us) |
**now** | `uint32_t now()` | returns the current timestamp (in us)|
**get_rssi** | `int get_rssi()` | returns the RSSI of last received packet |
**copy_header** | `void copy_header(uint8_t * dst)` | copy the 2-bytes long header of last received packet  |
**is_rx_done** | `bool is_rx_done()` | returns a boolean indicating if a packet has been received |
**copy_buffer** | `void copy_buffer(uint8_t * dst, uint8_t size)` | copy the buffer of last received packet |
**is_crc_good** | `bool is_crc_good()` | returns a boolean indicating the CRC validity of last received packet |
**get_current_gap_role** | `uint8_t get_current_gap_role()` | returns the current GAP role |
**copy_own_bd_addr** | `void copy_own_bd_addr(uint8_t * dst)` | copy the BD Address currently used by the controller |
**get_channel** | `uint8_t get_channel()` | returns the channel of the last received packet|
**get_current_channel** | `uint8_t get_current_channel()` | returns the current channel |
**is_slave** | `bool is_slave()` | returns a boolean indicating if the controller acts as a slave |
**copy_channel_map** | `void copy_channel_map(uint8_t * dst)` | copy the channel map of the current connection |
**get_hop_interval** | `uint16_t get_hop_interval()` | returns the hop interval of the current connection |
**get_crc_init** | `uint32_t get_crc_init()` | returns the CRC Init of the current connection |
**copy_access_addr** | `void copy_access_addr(uint32_t * dst)` | returns the Access Address of the current connection |
**start_scan** | `void start_scan()` | starts a scan operation |
**stop_scan** | `void stop_scan()` | stops a scan operation |
**log** | `void log(uint8_t *buffer, uint8_t size)` | transmit a log message |

If you want to include a specific part of the code only if the **SCAN** or the **CONNECTION** dependency are needed, you can use the following snippets:
```c
#ifdef SCAN_ENABLED
// This code will only be included if the SCAN dependency is needed
#endif

#ifdef CONNECTION_ENABLED
// This code will only be included if the CONNECTION dependency is needed
#endif
```  
* *patch.conf* describes the patches and modifications to the native firmware that are needed to instrument it. You can use three different syntax:

If you want to replace a specific instruction of the native firmware by a redirection to one of your wrapper's function:

```
<dependency>:<memory location>:<hook name>:<address to modify>:<wrapper function>:<old instruction>
```

For example, this line will insert a hook named **hook_on_scan_rx** in the ROM by replacing the instruction *bl 0xAE706* at address 0x75A38 by a redirection to the wrapper function *on_scan_rx* (if the **SCAN** dependency is selected):

```
SCAN:rom:hook_on_scan_rx:0x75a38:on_scan_rx:bl 0xae706
```

When this address will be reached, the execution flow will be redirected to a trampoline function (automatically generated during the build process), allowing to execute the wrapper function, execute the old instruction and redirect the execution flow to the native firmware.

You can also replace a value into memory by another one using the following syntax:

```
<dependency>:<memory location>:<hook name>:<address to modify>:<new value>
```

For example, the following line will write 0x20000700 at 0x1b000 in the ROM:
```
COMMON:rom:hook_injected_stack_pointer1:0x1b000:0x00700020
```

Finally, you can also use the following syntax to replaced a value into memory by a pointer to one of your wrapper functions:
```
<dependency>:<memory location>:<hook name>:<address to modify>:<wrapper function>
```

For example, the following line will insert a function pointer pointing to *on_timer_interrupt* function in wrapper.c at address 0x1B068 in ROM:

```
COMMON:rom:hook_on_timer_interrupt:0x1b068:on_timer_interrupt
```

### Configuration file

A configuration file named *target.conf* must also be implemented. It allows to describe several informations linked to the target and will be used by the Oasis tools. You have to provide the following informations:

| Information              | Description|
|--------------------------|:----------:|
name|name of the target
code_start|start address of code memory zone
code_size|size of code memory zone
data_start|start address of data memory zone
data_size|size of data memory zone
heap_size|size of the heap
rom_start|ROM memory start address
rom_end|ROM memory end address
ram_start|RAM memory start address
ram_end|ROM memory end address
interface_type|type of backend interface to use
architecture|architecture type
file_type|firmware type (hex or bin)
gcc_flags|additional GCC flags to append during build process


For example:

```
name:cyw20735
code_start:0x271770
code_size:0x2000
data_start:0x273770
data_size:0x1000
heap_size:0x800
rom_start:0x0
rom_end:0x2003ff
ram_start:0x200400
ram_end:0x283fff
interface_type:INTERNALBLUE_HCI
architecture:armv7-m
file_type:bin
gcc_flags:
```
