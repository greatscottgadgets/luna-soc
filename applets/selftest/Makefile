#
# This file is part of LUNA.
#

# - configuration -------------------------------------------------------------

UART	?= /dev/ttyACM0
CROSS	?= riscv64-unknown-elf

AR		= $(CROSS)-ar
CC		= $(CROSS)-gcc
OBJCOPY = $(CROSS)-objcopy

TARGET	= selftest
SOC		= top.py

# - firmware ------------------------------------------------------------------

CFLAGS	= -I./build/genc/ \
		  -march=rv32im \
		  -mabi=ilp32 \
		  -g \
		  -Os

LDFLAGS = -L./build/genc/ \
		  -Tsoc.ld \
		  -T$(TARGET).ld \
		  -nostdlib

SOURCES = \
	start.c \
	$(TARGET).c \
	platform.c \
	uart.c \
	ulpi.c \
	psram.c

$(TARGET).o: build/genc/soc.ld build/genc/resources.h $(SOURCES) $(TARGET).ld
	$(CC) $(CFLAGS) $(LDFLAGS) $(SOURCES) -o $@

$(TARGET).bin: $(TARGET).o
	$(OBJCOPY) -O binary $< $@

# - generated files -----------------------------------------------------------

build/genc/resources.h: $(SOC)
	mkdir -p build/genc/
	./$(SOC) --generate-c-header > $@

build/genc/soc.ld: $(SOC)
	mkdir -p build/genc/
	./$(SOC) --generate-ld-script > $@

# - gateware ------------------------------------------------------------------

$(TARGET).bit: $(TARGET).bin $(SOC)
	./$(SOC) --dry-run --output $@

# - helpers -------------------------------------------------------------------

clean:
	rm -f $(TARGET).elf $(TARGET).o $(TARGET).bin $(TARGET).bit
	rm -rf build/

# Loads the SoC bitstream running the selftest firmware onto our FPGA.
program: $(TARGET).bit
	-apollo configure $(TARGET).bit

# Loads the SoC bitstream running the selftest firmware onto our FPGA and shows the output in a console.
run: $(TARGET).bit
	-apollo configure $(TARGET).bit
	pyserial-miniterm $(UART) 115200
