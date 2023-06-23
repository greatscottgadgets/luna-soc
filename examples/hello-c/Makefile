SHELL := /bin/zsh

UART := /dev/cu.usbmodem22401
YOSYS_BIN := ~/GreatScott/gsg.git/cynthion/toolchain/oss-cad-suite/bin

AR := riscv64-unknown-elf-ar
CC := riscv64-unknown-elf-gcc
OBJCOPY := riscv64-unknown-elf-objcopy

# - gateware ------------------------------------------------------------------

gateware:
	rm -rf build
	PATH=$(PATH):$(YOSYS_BIN) AR=$(AR) python top.py

load:
	-apollo configure build/top.bit

load-ulx3s:
	PATH=$(PATH):$(YOSYS_BIN) openFPGALoader --board ulx3s build/top.bit

# - firmware -----------------------------------------------------------------

CFLAGS	= -march=rv32i -mabi=ilp32 -g -Os -I./build/genc/
LDFLAGS = -Tbuild/genc/soc.ld -Triscv_application.ld  -nostdlib -L./build/genc/

firmware.elf: main.c start.S riscv_application.ld build/genc/soc.ld
	$(CC) $(CFLAGS) $(LDFLAGS) start.S main.c -o $@

firmware.bin: firmware.elf
	$(OBJCOPY) -O binary $< $@

firmware: firmware.bin

# - helpers -------------------------------------------------------------------

LXTERM := litex_term --kernel firmware.bin --kernel-adr 0x40000000 --speed 115200 $(UART)

run: firmware.bin
	-apollo configure build/top.bit
	expect -c "spawn $(LXTERM); send \nserialboot\n; interact"

clean:
	-rm -rf *.elf *.bin

distclean: clean
	-rm -rf build/
