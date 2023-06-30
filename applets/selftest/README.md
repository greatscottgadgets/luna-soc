# LunaSoC selftest applet

A simple selftest applet for LUNA-SOC designs.

This applet is designed for the Great Scott Gadgets Cynthion but it should be relatively easy to adapt to other devices.


## Dependencies

### Yosys Toolchain

Grab and install the latest toolchain from:

    https://github.com/YosysHQ/oss-cad-suite-build/releases/latest

Remember to mollify Gatekeeper if you're on macOS:

    oss-cad-suite/activate

Enable environment with:

    source <path-to>/oss-cad-suite/environment

### RiscV GNU Toolchain

You will need this to build the selftest firmware:

    # macOS - https://github.com/riscv-software-src/homebrew-riscv
    brew tap riscv-software-src/riscv
    brew install riscv-gnu-toolchain

    # debian
    apt install gcc-riscv64-unknown-elf


## Running the applet

Assuming all dependencies are in order you can run the selftest applet with:

    make run

If the UART of your device is on a different port to `/dev/ttyACM0` you may want to specify it as well. For example:

    UART=/dev/cu.usbmodem22401 make run
