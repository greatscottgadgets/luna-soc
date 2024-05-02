SHELL := /bin/zsh

# - configuration -------------------------------------------------------------

UART	?= /dev/ttyACM0
CROSS	?= riscv64-unknown-elf

CC := $(CROSS)-gcc
OBJCOPY := $(CROSS)-objcopy

# - firmware -----------------------------------------------------------------

CFLAGS	= -march=rv32i -mabi=ilp32 -g -Os -I./build/genc/
LDFLAGS = -Tbuild/genc/soc.ld -Triscv_application.ld  -nostdlib -L./build/genc/

firmware.elf: main.c start.S riscv_application.ld build/genc/soc.ld
	$(CC) $(CFLAGS) $(LDFLAGS) start.S main.c -o $@

firmware.bin: firmware.elf
	$(OBJCOPY) -O binary $< $@

firmware: build/genc/resources.h build/genc/soc.ld firmware.bin

# - generated files -----------------------------------------------------------

build/genc/resources.h: top.py
	mkdir -p build/genc/
	python top.py --generate-c-header > $@

build/genc/soc.ld: top.py
	mkdir -p build/genc/
	python top.py --generate-ld-script > $@

# - gateware ------------------------------------------------------------------

gateware: top.py
	python top.py --dry-run --output top.bit

load:
	-apollo configure top.bit

load-ulx3s:
	openFPGALoader --board ulx3s top.bit

# - helpers -------------------------------------------------------------------

clean:
	-rm -rf build/ firmware.elf firmware.bin

# Loads the SoC bitstream running the selftest firmware onto our FPGA.
program: firmware gateware
	-apollo configure top.bit

# Loads the SoC bitstream running the selftest firmware onto our FPGA and shows the output in a console.
run: firmware gateware
	-apollo configure top.bit
	pyserial-miniterm $(UART) 115200
