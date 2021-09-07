BUILD_DIR := build
SRC_DIR := src
APP_DIR := app
INCLUDE_DIR := include

CFLAGS += -nostdlib
CFLAGS += -nostartfiles
CFLAGS += -mthumb
CFLAGS += -march=armv7-m
CFLAGS += -ffreestanding
CFLAGS += -ffunction-sections
CFLAGS += -fdata-sections
CFLAGS += -O0

INTERFACE := $(shell python3 scripts/detect_interface.py)

ifeq ($(PLATFORM),)
    PLATFORM = BOARD_CYW20735
endif
SUPPORTED_PLATFORMS = BOARD_CYW20735 BOARD_BCM43430A1 BOARD_BCM4335C0

ifeq ($(filter $(PLATFORM), $(SUPPORTED_PLATFORMS)),)
    $(error "PLATFORM not in $(SUPPORTED_PLATFORMS)")
endif

ifeq ($(PLATFORM),BOARD_CYW20735)
	CONF_DIR := boards/cyw20735
endif

ifeq ($(PLATFORM),BOARD_BCM43430A1)
	CONF_DIR := boards/bcm43430a1
endif

ifeq ($(PLATFORM),BOARD_BCM4335C0)
	CONF_DIR := boards/bcm4335c0
endif

APPS = btlejack
APPS_SRC = $(foreach app,$(APPS), $(APP_DIR)/$(app)/app.c)
APPS_OBJ = $(foreach app,$(APPS), $(BUILD_DIR)/$(APP_DIR)/$(app)/app.o)
APPS_BUILD = $(foreach app,$(APPS), $(BUILD_DIR)/$(APP_DIR)/$(app))

all : build

create_builddir:
	mkdir -p $(BUILD_DIR)
	mkdir -p $(APPS_BUILD)

$(BUILD_DIR)/$(APP_DIR)/%/app.o: $(APP_DIR)/%/app.c
	arm-none-eabi-gcc $< $(CFLAGS) -c -o $@ -I $(INCLUDE_DIR) 

$(BUILD_DIR)/app.c: $(APPS_OBJ)
	python3 scripts/generate_app.py $(BUILD_DIR) $(APPS)
	
$(BUILD_DIR)/hooks.c: $(CONF_DIR)/patch.conf
	python3 scripts/generate_hooks.py $(BUILD_DIR) $(CONF_DIR)/patch.conf
	
$(BUILD_DIR)/out.elf: $(BUILD_DIR)/app.c $(APPS_OBJ) $(SRC_DIR)/*.c $(SRC_DIR)/**/*.c $(BUILD_DIR)/hooks.c $(CONF_DIR)/functions.c
	arm-none-eabi-gcc -D$(PLATFORM) $(BUILD_DIR)/app.c $(APPS_OBJ) $(SRC_DIR)/*.c $(SRC_DIR)/**/*.c $(BUILD_DIR)/hooks.c $(CFLAGS) $(CONF_DIR)/functions.c -T $(CONF_DIR)/linker.ld $(CONF_DIR)/functions.ld -o $(BUILD_DIR)/out.elf -I $(INCLUDE_DIR) 

$(BUILD_DIR)/symbols.sym: $(BUILD_DIR)/out.elf
	arm-none-eabi-nm -S -a $(BUILD_DIR)/out.elf | sort > $(BUILD_DIR)/symbols.sym	
	
$(BUILD_DIR)/patches.csv: $(BUILD_DIR)/symbols.sym
	python3 scripts/generate_patches.py $(BUILD_DIR)/out.elf $(BUILD_DIR)/symbols.sym $(CONF_DIR)/patch.conf $(BUILD_DIR) 2> /dev/null
		
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
	sudo scripts/logger.py
