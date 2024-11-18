# LUNA-SOC: Amaranth HDL library for building USB-capable SoC designs

## LUNA-SOC Library

LUNA-SOC is a toolkit for building custom SoC (System on Chip) designs incorporating [LUNA](https://github.com/greatscottgadgets/luna) USB peripherals.

Some things you can use LUNA-SOC for, currently:

* Implement SoC designs using a [Minerva](https://github.com/minerva-cpu/minerva) or [VexRiscv](https://github.com/SpinalHDL/VexRiscv) RISC-V CPU.
* Add a variety of Wishbone and CSR peripherals to your SoC design such as: SRAM, GPIO, UART and USB.
* Implement firmware for your designs using Rust or C.

> __NOTE__
> There are no official packages for Minerva at the time of writing but you can install it directly from the repository using:
>
> `pip install git+https://github.com/minerva-cpu/minerva`

## Project Structure

This project is broken down into several directories:

* [`luna_soc/`](luna_soc/) -- the primary LUNA-SOC library; generates gateware and provides peripherals.
* [`examples/`](examples/) -- some simple LUNA-SOC examples demonstrating gateware design and firmware implementation.
* [`docs/`](docs/) -- sources for the LUNA-SOC Sphinx documentation.


## Project Documentation

LUNA-SOC's documentation is captured on [Read the Docs](https://luna-soc.readthedocs.io/en/latest/). Raw documentation sources are in the docs folder.
