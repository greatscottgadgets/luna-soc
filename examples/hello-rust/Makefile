SHELL := /bin/zsh

YOSYS_BIN := ~/GreatScott/gsg.git/cynthion/toolchain/oss-cad-suite/bin
AR=riscv64-unknown-elf-ar

# - gateware ------------------------------------------------------------------

gateware:
	rm -rf build
	PATH=$(PATH):$(YOSYS_BIN) AR=$(AR) python top.py
	cp build/genrust/memory.x .

load:
	-apollo configure build/top.bit

load-ulx3s:
	PATH=$(PATH):$(YOSYS_BIN) openFPGALoader --board ulx3s build/top.bit

# - firmware -----------------------------------------------------------------

firmware:
	cargo build

# - helpers -------------------------------------------------------------------

run:
	cargo run

clean:
	-rm -rf build/ resources.h soc.ld
