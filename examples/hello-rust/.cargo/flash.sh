#!/usr/bin/env zsh

# uart configuration - check that this is right for your machine
case `uname` in
    Darwin)
        UART=/dev/cu.usbmodem22401
    ;;
    Linux)
        UART=/dev/ttyACM0
    ;;
esac
echo "Using board UART=$UART"

# bitstream
BASE_MEM=0x40000000
BITSTREAM=build/top.bit

# create bin file
NAME=$(basename $1)
cargo objcopy --release --bin $NAME -- -Obinary $1.bin

# lxterm command
LXTERM="litex_term --kernel $1.bin --kernel-adr $BASE_MEM --speed 115200 $UART"

# configure cynthion fpga with soc bitstream
echo "Configuring fpga: $BITSTREAM"
apollo configure $BITSTREAM 2>/dev/null

# flash firmware to soc
echo "Flashing: $1.bin"
expect -c "spawn $LXTERM; send \nserialboot\n; interact"
