# Installation

> **_NOTE:_** This tool has been only tested on Linux, and probably requires some minor modifications to run on another operating system.
## Installing the dependencies

First, you need to install the following dependencies:

| Package                    | Recommended version      |
|----------------------------|:------------------------:|
| nrfutil                    |  6.1.3                   |
| scapy                      |  2.4.5                   |
| internalblue               |  latest                  |
| openocd                    |  0.11.0                  |
| GNU ARM Embedded Toolchain |  11.1.0                  |

### NRFUtil

Installing nrfutil is straightforward with pip:

`pip install nrfutil`

### Scapy

Installing scapy with pip is quite easy too:

`pip install scapy`

### Internalblue
Similarly, the following command will install internalblue on your system:

`pip install https://github.com/seemoo-lab/internalblue/archive/master.zip`

### OpenOCD
To install OpenOCD, you can use the standard package manager of your distribution:

* **Ubuntu-based distributions:**

`sudo apt install openocd`

* **Fedora distribution:**

`sudo dnf install openocd`

* **ARCH-based distributions:**

`sudo pacman -S openocd`

### GNU ARM Embedded Toolchain
You can install the GNU ARM Embedded Toolchain easily from your standard package manager:

* **Ubuntu-based distributions:**

`sudo apt install binutils-arm-none-eabi gcc-arm-none-eabi`

* **Fedora distribution:**

`sudo dnf install arm-none-eabi-binutils-cs arm-none-eabi-gcc-cs`

* **ARCH-based distributions:**

`sudo pacman -S arm-none-eabi-binutils arm-none-eabi-gcc`

### Documentation (optional)
If you want to build the documentation by yourself, install mkdocs and mkdocs-material:

`sudo pip3 install mkdocs mkdocs-material`

## Installing Oasis

You don't have anything to install to use Oasis ! Just clone the repository and you can get started:

`git clone https://github.com/RCayre/oasis`

# Path customization (optional)

By default, Oasis will rely on the PATH environment variable to find the various tools it needs.
If for some reason you want to provide a custom path, please modify oasis.conf file and provide your own path using the following syntax :
```
openocd:/usr/bin/openocd
nrfutil:/usr/local/bin/nrfutil
python3:/usr/bin/python3
arm_gcc:/usr/bin/arm-none-eabi-gcc
arm_objcopy:/usr/bin/arm-none-eabi-objcopy
arm_objdump:/usr/bin/arm-none-eabi-objdump
arm_nm:/usr/bin/arm-none-eabi-nm
arm_ld:/usr/bin/arm-none-eabi-ld
arm_as:/usr/bin/arm-none-eabi-as
```
