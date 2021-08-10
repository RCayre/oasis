BUILD_DIR := build
SRC_DIR := src

CFLAGS += -nostdlib
CFLAGS += -nostartfiles
CFLAGS += -mthumb
CFLAGS += -march=armv7-m
CFLAGS += -ffreestanding
CFLAGS += -ffunction-sections
CFLAGS += -fdata-sections

INTERFACE := $(shell python3 scripts/detect_interface.py)

ifeq ($(PLATFORM),)
    PLATFORM = BOARD_CYW20735
endif
SUPPORTED_PLATFORMS = BOARD_CYW20735

ifeq ($(filter $(PLATFORM), $(SUPPORTED_PLATFORMS)),)
    $(error "PLATFORM not in $(SUPPORTED_PLATFORMS)")
endif

ifeq ($(PLATFORM),BOARD_CYW20735)
	CONF_DIR := boards/cyw20735
endif

default : build

create_builddir:
	mkdir -p $(BUILD_DIR)
	
$(BUILD_DIR)/hooks.c: $(CONF_DIR)/patch.conf
	python3 scripts/generate_hooks.py $(BUILD_DIR) $(CONF_DIR)/patch.conf
	
$(BUILD_DIR)/out.elf: $(SRC_DIR)/*.c $(BUILD_DIR)/hooks.c
	arm-none-eabi-gcc $(SRC_DIR)/*.c $(BUILD_DIR)/hooks.c $(CFLAGS) -T $(CONF_DIR)/linker.ld $(CONF_DIR)/functions.ld -o $(BUILD_DIR)/out.elf -I include

$(BUILD_DIR)/symbols.sym: $(BUILD_DIR)/out.elf
	arm-none-eabi-nm -S $(BUILD_DIR)/out.elf | sort > $(BUILD_DIR)/symbols.sym	
	
$(BUILD_DIR)/patches.csv: $(BUILD_DIR)/symbols.sym
	python3 scripts/generate_patches.py $(BUILD_DIR)/out.elf $(BUILD_DIR)/symbols.sym $(CONF_DIR)/patch.conf $(BUILD_DIR)
		
build: create_builddir $(BUILD_DIR)/patches.csv

patch: build
	sudo python3 $(CONF_DIR)/patcher.py $(BUILD_DIR)/patches.csv
	rm -f btsnoop.log
	
clean:
	rm -rf build

attach:
	@stty -F $(INTERFACE) 3000000
	@btattach -B $(INTERFACE) &
	@sleep 1
	@hciconfig | grep hci1 -n1 | grep BD | awk '{print $$3" "$$4}'

detach:
	@pkill btattach
