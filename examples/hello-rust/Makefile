SHELL := /bin/zsh

# - configuration -------------------------------------------------------------

CROSS	?= riscv64-unknown-elf

AR := $(CROSS)-ar

# - gateware ------------------------------------------------------------------

gateware:
	rm -rf build
	AR=$(AR) python top.py
	cp build/genrust/memory.x .

load:
	-apollo configure build/top.bit

load-ulx3s:
	openFPGALoader --board ulx3s build/top.bit

# - firmware -----------------------------------------------------------------

firmware:
	cargo build

# - helpers -------------------------------------------------------------------

run:
	cargo run

clean:
	-rm -rf build/ resources.h soc.ld
