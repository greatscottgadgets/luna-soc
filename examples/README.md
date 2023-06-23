# LUNA-SOC Examples

## Dependencies

### Yosys Toolchain

Grab and install the latest toolchain from:

    https://github.com/YosysHQ/oss-cad-suite-build/releases/latest

Remember to mollify Gatekeeper if you're on macOS:

    oss-cad-suite/activate

Enable environment with:

    source <path-to>/oss-cad-suite/environment


### Rust

If you'd like to use `rustup` to manage your Rust environment you can install it with:

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

Install riscv target support:

    rustup target add riscv32imac-unknown-none-elf

Install cargo binutils support:

    rustup component add llvm-tools-preview
    cargo install cargo-binutils


### RiscV GNU Toolchain

This is needed to build litex-bios and any C examples:

    # macOS - https://github.com/riscv-software-src/homebrew-riscv
    brew tap riscv-software-src/riscv
    brew install riscv-gnu-toolchain

    # debian
    apt install gcc-riscv64-unknown-elf
