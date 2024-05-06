SHELL := /bin/zsh

# - firmware -----------------------------------------------------------------

firmware: firmware.bin

firmware.bin: memory.x
	cargo objcopy --release -- -Obinary firmware.bin


# - generated files -----------------------------------------------------------

memory.x: $(SOC)
	python top.py --generate-memory-x > $@


# - gateware ------------------------------------------------------------------

gateware: firmware.bin top.py
	python ./top.py --dry-run --output top.bit
	rm firmware.bin


# - helpers -------------------------------------------------------------------

clean:
	-cargo clean
	-rm -rf memory.x firmware.bin top.bit build/

# Loads the SoC bitstream running the selftest firmware onto our FPGA.
program: firmware gateware
	-apollo configure top.bit

program-ulx3s:
	openFPGALoader --board ulx3s top.bit

# Loads the SoC bitstream running the selftest firmware onto our FPGA and shows the output in a console.
run: firmware gateware
	-apollo configure top.bit
	pyserial-miniterm $(UART) 115200
