# - svd ----------------------------------------------------------------------

svd:
	python ./top.py --generate-svd > lunasoc-pac/svd/lunasoc.svd


# - pac ----------------------------------------------------------------------

pac: svd
	mkdir -p build
	rm -rf lunasoc-pac/src/generated.rs lunasoc-pac/src/generated/
	svd2rust -i lunasoc-pac/svd/lunasoc.svd -o build/ --target riscv --make_mod --ident-formats-theme legacy
	mv build/mod.rs lunasoc-pac/src/generated.rs
	mv build/device.x lunasoc-pac/

	form -i lunasoc-pac/src/generated.rs -o lunasoc-pac/src/generated/
	mv lunasoc-pac/src/generated/lib.rs lunasoc-pac/src/generated.rs
	cargo fmt -p lunasoc-pac -- --emit files


# - firmware -----------------------------------------------------------------

firmware: pac firmware.bin

firmware.bin: memory.x
	cargo objcopy --release -- -Obinary build/firmware.bin


# - generated files -----------------------------------------------------------

memory.x: $(SOC)
	python top.py --generate-memory-x > $@


# - gateware ------------------------------------------------------------------

gateware: firmware top.py
	python ./top.py --dry-run --output build/top.bit
	rm build/firmware.bin


# - helpers -------------------------------------------------------------------

# Loads the SoC bitstream running the selftest firmware onto our FPGA.
program: firmware gateware
	-apollo configure build/top.bit

program-ulx3s:
	openFPGALoader --board ulx3s build/top.bit

# Loads the SoC bitstream running the selftest firmware onto our FPGA and shows the output in a console.
run: firmware gateware
	-apollo configure build/top.bit
	pyserial-miniterm $(UART) 115200

clean:
	-cargo clean
	-rm -rf memory.x build/
	-rm -rf lunasoc-pac/device.x lunasoc-pac/svd/lunasoc.svd lunasoc-pac/src/generated.rs lunasoc-pac/src/generated/
