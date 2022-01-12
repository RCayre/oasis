BUILD_DIR := build
SOURCE_DIR := src
INCLUDE_DIR := include
MODULES_DIR := modules
SCRIPTS_DIR := scripts
TARGETS_DIR := targets
MAPS_DIR := maps


ifneq ($(MAKECMDGOALS),generate_target)
ifneq ($(MAKECMDGOALS),clean)

# Checks the existence of the provided target
SUPPORTED_TARGETS := $(shell ls $(TARGETS_DIR))

# if no target is provided, use the first one as default
ifeq ($(TARGET),)
  TARGET := $(shell echo $(SUPPORTED_TARGETS) | awk '{print $$1}')
  $(warning No target specified, using $(TARGET) as default target.)
endif


ifeq ($(MAKECMDGOALS),attach)
ifeq ($(TARGET),cyw20735)
  CYW20735_TTY := $(shell python3 $(SCRIPTS_DIR)/detect_cyw20735_ttyUSB.py)
else ifneq ($(TARGET),cyw20735)
  $(error Attach is only necessary for target 'cyw20735')
endif
endif

ifeq ($(filter $(TARGET), $(SUPPORTED_TARGETS)),)
  $(error "Provided target ($(TARGET)) not in $(SUPPORTED_TARGETS).")
endif

# Get target informations
TARGET_DIR := $(TARGETS_DIR)/$(TARGET)

CODE_START := $(shell python3 $(SCRIPTS_DIR)/extract_target_info.py $(TARGET) code_start)
CODE_SIZE := $(shell python3 $(SCRIPTS_DIR)/extract_target_info.py $(TARGET) code_size)

DATA_START := $(shell python3 $(SCRIPTS_DIR)/extract_target_info.py $(TARGET) data_start)
DATA_SIZE := $(shell python3 $(SCRIPTS_DIR)/extract_target_info.py $(TARGET) data_size)

HEAP_SIZE := $(shell python3 $(SCRIPTS_DIR)/extract_target_info.py $(TARGET) heap_size)

# Get target architecture and compilation flags
ARCH := $(shell python3 $(SCRIPTS_DIR)/extract_target_info.py $(TARGET) architecture)

CFLAGS += -nostdlib
CFLAGS += -nostartfiles
CFLAGS += -mthumb
CFLAGS += -march=$(ARCH)
CFLAGS += -ffreestanding
CFLAGS += -ffunction-sections
CFLAGS += -fdata-sections
CFLAGS += -O0
CFLAGS += $(shell python3 $(SCRIPTS_DIR)/extract_target_info.py $(TARGET) gcc_flags)


MODULES_SRC = $(foreach module,$(MODULES), $(MODULES_DIR)/$(module)/module.c)
MODULES_OBJ = $(foreach module,$(MODULES), $(BUILD_DIR)/$(MODULES_DIR)/$(module)/module.o)
MODULES_BUILD = $(foreach module,$(MODULES), $(BUILD_DIR)/$(MODULES_DIR)/$(module))

DEPENDENCIES = $(shell python3 $(SCRIPTS_DIR)/extract_dependencies.py $(MODULES))
DEPENDENCIES_GCC_GLAGS = $(foreach dependency,$(DEPENDENCIES), -D$(dependency)_ENABLED)
endif
endif

all: build
default: build

clean_internalblue_logs:
	rm -rf internalblue*
	rm -rf btsnoop.log

$(MODULES_BUILD):
	mkdir -p $(MODULES_BUILD)

create_build_directory: $(MODULES_BUILD)
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/$(MODULES_DIR)/%/module.o: $(MODULES_DIR)/%/module.c
	arm-none-eabi-gcc $< $(CFLAGS) -c -o $@ -I $(INCLUDE_DIR)

$(BUILD_DIR)/callbacks.c: $(MODULES_OBJ)
	python3 $(SCRIPTS_DIR)/generate_callbacks.py $(MODULES)

$(BUILD_DIR)/trampolines.c: $(TARGET_DIR)/patch.conf
	python3 $(SCRIPTS_DIR)/generate_trampolines.py $(TARGET) $(DEPENDENCIES)

$(BUILD_DIR)/out.elf: $(BUILD_DIR)/callbacks.c $(MODULES_OBJ) $(SOURCE_DIR)/*.c $(SOURCE_DIR)/**/*.c $(BUILD_DIR)/trampolines.c $(TARGET_DIR)/wrapper.c
	arm-none-eabi-gcc $(DEPENDENCIES_GCC_GLAGS) -DHEAP_SIZE=$(HEAP_SIZE) $(BUILD_DIR)/callbacks.c $(MODULES_OBJ) $(SOURCE_DIR)/*.c $(SOURCE_DIR)/**/*.c $(BUILD_DIR)/trampolines.c $(CFLAGS) $(TARGET_DIR)/wrapper.c -T $(TARGET_DIR)/linker.ld $(TARGET_DIR)/functions.ld -o $(BUILD_DIR)/out.elf -I $(INCLUDE_DIR) -Wl,"--defsym=CODE_START=$(CODE_START)" -Wl,"--defsym=CODE_SIZE=$(CODE_SIZE)" -Wl,"--defsym=DATA_START=$(DATA_START)"  -Wl,"--defsym=DATA_SIZE=$(DATA_SIZE)"

$(BUILD_DIR)/symbols.sym: $(BUILD_DIR)/out.elf
	arm-none-eabi-nm -S -a $(BUILD_DIR)/out.elf | sort > $(BUILD_DIR)/symbols.sym

$(BUILD_DIR)/patches.csv: $(BUILD_DIR)/symbols.sym
	python3 $(SCRIPTS_DIR)/generate_patches.py $(TARGET) $(DEPENDENCIES)
	cp $(BUILD_DIR)/patches.csv $(MAPS_DIR)/$(TARGET).csv

build: clean create_build_directory $(BUILD_DIR)/patches.csv

attach:
	sudo stty -F $(CYW20735_TTY) 3000000
	sudo btattach -B $(CYW20735_TTY) &
	sleep 1
	sudo hciconfig | grep hci0 -n1 | grep BD | awk '{print $$3" "$$4}'

patch:
	python3 $(SCRIPTS_DIR)/patch_target.py $(TARGET)

clean: clean_internalblue_logs
	rm -rf build

log:
	python3 $(SCRIPTS_DIR)/interact.py $(TARGET) log
