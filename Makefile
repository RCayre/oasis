BUILD_DIR := build
SRC_DIR := src
APP_DIR := app
SCRIPTS_DIR := scripts
INCLUDE_DIR := include

INTERFACE := $(shell python3 $(SCRIPTS_DIR)/detect_interface.py)

ifeq ($(PLATFORM),)
    PLATFORM = BOARD_CYW20735
endif
SUPPORTED_PLATFORMS = BOARD_CYW20735 BOARD_BCM43430A1 BOARD_BCM4335C0 BOARD_BCM4345C0 BOARD_NRF52840 BOARD_NRF51

ifeq ($(filter $(PLATFORM), $(SUPPORTED_PLATFORMS)),)
    $(error "$(PLATFORM) not in $(SUPPORTED_PLATFORMS)")
endif

ifeq ($(PLATFORM),BOARD_CYW20735) # CYW20735 Development board
	CONF_DIR := boards/cyw20735
	CORE_TYPE := HCI
	GENERATE_CONF := cp
	HEAP_SIZE := 0x1000
endif

ifeq ($(PLATFORM),BOARD_BCM43430A1) # Raspberry Pi 3
	CONF_DIR := boards/bcm43430a1
	CORE_TYPE := HCI
	GENERATE_CONF := cp
	HEAP_SIZE := 0x1000
endif

ifeq ($(PLATFORM),BOARD_BCM4335C0) # Nexus 5
	CONF_DIR := boards/bcm4335c0
	CORE_TYPE := ADB
	GENERATE_CONF := cp
	HEAP_SIZE := 0x1000
endif

ifeq ($(PLATFORM),BOARD_BCM4345C0) # Raspberry Pi 3+/4
	CONF_DIR := boards/bcm4345c0
	CORE_TYPE := HCI
	GENERATE_CONF := cp
	HEAP_SIZE := 0x1000
endif

ifeq ($(PLATFORM),BOARD_NRF52840) # NRF52840 with (Zephyr hci_usb)
	CONF_DIR := boards/nrf52840
	GENERATE_CONF := cp
	HEAP_SIZE := 0x1000
endif


ifeq ($(PLATFORM),BOARD_NRF51) # NRF52840 with SoftDevice
	CONF_DIR := boards/nrf51
	GENERATE_CONF := python3 $(CONF_DIR)/generate_conf.py
	HEAP_SIZE := 0x800
endif


CFLAGS += -nostdlib
CFLAGS += -nostartfiles
CFLAGS += -mthumb
CFLAGS += -march=armv7-m
CFLAGS += -ffreestanding
CFLAGS += -ffunction-sections
CFLAGS += -fdata-sections
CFLAGS += -O0

APPS = gattacker
APPS_SRC = $(foreach app,$(APPS), $(APP_DIR)/$(app)/app.c)
APPS_OBJ = $(foreach app,$(APPS), $(BUILD_DIR)/$(APP_DIR)/$(app)/app.o)
APPS_BUILD = $(foreach app,$(APPS), $(BUILD_DIR)/$(APP_DIR)/$(app))

DEPENDENCIES = $(shell python3 $(SCRIPTS_DIR)/generate_dependencies.py $(APPS))

all : build

create_builddir:
	mkdir -p $(BUILD_DIR)
	mkdir -p $(APPS_BUILD)

$(BUILD_DIR)/$(APP_DIR)/%/app.o: $(APP_DIR)/%/app.c
	arm-none-eabi-gcc $< $(CFLAGS) -c -o $@ -I $(INCLUDE_DIR)

$(BUILD_DIR)/app.c: $(APPS_OBJ)
	python3 $(SCRIPTS_DIR)/generate_app.py $(BUILD_DIR) $(APPS)

 $(BUILD_DIR)/patch.conf:  $(CONF_DIR)/patch.conf
	$(GENERATE_CONF) $(CONF_DIR)/patch.conf $(BUILD_DIR)/patch.conf

$(BUILD_DIR)/hooks.c: $(BUILD_DIR)/patch.conf
	python3 $(SCRIPTS_DIR)/generate_hooks.py $(BUILD_DIR) $(CONF_DIR)/patch.conf $(DEPENDENCIES)

$(BUILD_DIR)/out.elf: $(BUILD_DIR)/app.c $(APPS_OBJ) $(SRC_DIR)/*.c $(SRC_DIR)/**/*.c $(BUILD_DIR)/hooks.c $(CONF_DIR)/functions.c
	arm-none-eabi-gcc -DHEAP_SIZE=$(HEAP_SIZE) -D$(PLATFORM) $(BUILD_DIR)/app.c $(APPS_OBJ) $(SRC_DIR)/*.c $(SRC_DIR)/**/*.c $(BUILD_DIR)/hooks.c $(CFLAGS) $(CONF_DIR)/functions.c -T $(CONF_DIR)/linker.ld $(CONF_DIR)/functions.ld -o $(BUILD_DIR)/out.elf -I $(INCLUDE_DIR)

$(BUILD_DIR)/symbols.sym: $(BUILD_DIR)/out.elf
	arm-none-eabi-nm -S -a $(BUILD_DIR)/out.elf | sort > $(BUILD_DIR)/symbols.sym

$(BUILD_DIR)/patches.csv: $(BUILD_DIR)/symbols.sym
	python3 $(SCRIPTS_DIR)/generate_patches.py $(BUILD_DIR)/out.elf $(BUILD_DIR)/symbols.sym $(CONF_DIR)/patch.conf $(BUILD_DIR) $(DEPENDENCIES) 2> /dev/null

build: clean create_builddir $(BUILD_DIR)/patches.csv

patch: build
	sudo python3 $(CONF_DIR)/patcher.py $(BUILD_DIR)/patches.csv
	rm -f btsnoop.log

clean:
	rm -rf build

disasm:
	arm-none-eabi-objdump -D $(BUILD_DIR)/out.elf

# cyw20735 management
attach:
	sudo stty -F $(INTERFACE) 3000000
	sudo btattach -B $(INTERFACE) &
	sleep 1
	sudo hciconfig | grep hci1 -n1 | grep BD | awk '{print $$3" "$$4}'

detach:
	sudo pkill btattach

reset:
	sudo hciconfig hci1 down
	sudo hciconfig hci1 up

# hci monitoring
dump:
	sudo hcidump -i hci1 -R

log:
	sudo $(SCRIPTS_DIR)/logger.py --interface=hci1
