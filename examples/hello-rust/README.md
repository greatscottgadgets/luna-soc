# hello-rust

A simple firmware example for LUNA-SOC written in Rust.


## Dependencies

Please ensure you've installed any required dependencies referenced in [`../examples/README.md`](../examples/README.md).


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
