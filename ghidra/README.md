# oasis-firmware-analyzer-ghidra-api
Use Ghidra API to automatize the pattern searching in the firmware analyzer module of the OASIS framework

# Folders
- `script/` : scripts who use the Ghidra API
- `tables/` : tables for different architecture (Broadcom (complete at 70%), NRF51-Softdevice, NRF52-Zephyr)

# How to use
1. Install Ghidra
2. Create a Ghidra Folder, import binary file, choose the language type (ARMv7 little endian) and run it for the first time to do the analyzis with ARM force options
3. Find `analyzeHeadless` executable (default location `/usr/share/ghidra/support/`)
4. How to use `analyzeHeadless` :
   
`
/usr/share/ghidra/support/analyzeHeadless <folder project Ghidra> <name project[/folder]> -noanalysis -process <binary> -postScript <script>
`

An example : 

`
/usr/share/ghidra/support/analyzeHeadless Ghidra/ FirmwareAnalyzis -noanalysis -process zephyr_nrf52_firmware.hex -postScript script/SearchPattern.py
`

5. Don't forget to change inside the `SearchPattern.py` script the table you want to use in order to target a specific architecture
6. Run the script at the same level than the README
7. See the results

# Scripts
- `SearchPattern.py` : script to search functions we want to target (use a custom similarity system)
- `GetInfos.py` : script to get informations about an instruction to fill a JSON table (replace the address you want to get informations inside Ghidra)

# Custom similarity system
1. Best result : __0__
2. Good result : __< 10__
3. Potential found functions (need to search manually the different candidates) :  __between 10 and 40__
4. Bad result : __> 50__

### Malus system based on what ?
- mnemonic instruction
- nb operands instruction
- type (BIT, ADDRESS, DATA, READ, WRITE, etc.)  operands instruction
- pcode constant fields values to represent mnemonic
- hexadecimal
- Pcode LOAD vs STORE
- Zephyr registers

# What is the FORCE MODE ?
When the script is running, it will search pattern only on the entry point of each function. But sometimes, pattern will be at different locations in the function.

So, for the first iteration, the script will analyze on the entry point for each pattern and if the result is not satisfy, it will re-run in the force mode (on every instruction for each function) to find a better candidate.

The only drawback is the execution time of this mode !

# JSON tables fields

    {
        "func": "<name of the target function>",
        "instr": "instruc1;instruc2;...;instrucN", (null sometimes)
        "hexa": "hex1 hex2 hex3 ... hexN",
        "diff": "<0 or 1>",
        "regs": "<zephyr register or null>",
        "specs": "null", (can be anything ...)
        "pcode": "<n1,n2,n3;...;n1,n2,n3>" (null sometimes)
    },

An example :

    {
        "func": "lm_getRawRssiWithTaskId",
        "instr": "add,2,(512:r0),(512:r1);sxtb,2,(512:r0),(512:r0);bx,1,(512:lr)",
        "hexa": "0844 40b2 7047",
        "diff": "0",
        "regs": "null",
        "specs": "null",
        "pcode": "19;63,18;27,12,1,27,10"
    }

# Future improvements
1. add new metrics to increase the accurary of the pattern searching
2. use the "specs" (specificities aspect of the target function) and "diff" (the function use different patterns) fields in the JSON table
