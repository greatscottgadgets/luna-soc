# hello-rust

A simple firmware example for LUNA-SOC written in Rust.

## Dependencies

Please ensure you've installed any required dependencies referenced in [`../examples/README.md`](../examples/README.md).


## Configuration

Edit the `Makefile` and set `YOSYS_BIN` to the location of your `oss-cad-suite` installation.

Edit `.cargo/flash.sh` and set `UART` to the port matching your board's UART.


## Running the example

### Step 1

Build the gateware with:

    make gateware

### Step 2

Build the firmware with:

    cargo build

### Step 3

Finally, run the example firmware with:

    cargo run

You should see a simple LED runner on your board with some logging output on the console.
