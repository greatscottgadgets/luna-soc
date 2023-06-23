#
# This file is part of LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

from luna                                        import configure_default_logging, top_level_cli
from luna.gateware.usb.usb2.device               import USBDevice

from luna_soc.gateware.soc                       import LunaSoC
from luna_soc.gateware.csr                       import GpioPeripheral, LedPeripheral

from amaranth                                    import Elaboratable, Module, Cat
from amaranth.hdl.rec                            import Record

from lambdasoc.cpu.minerva                       import MinervaCPU

import logging
import os
import sys

CLOCK_FREQUENCIES_MHZ = {
    'sync': 60
}

# - HelloSoc ------------------------------------------------------------------

class HelloSoc(Elaboratable):
    def __init__(self, clock_frequency):

        # create a stand-in for our UART
        self.uart_pins = Record([
            ('rx', [('i', 1)]),
            ('tx', [('o', 1)])
        ])

        # create our SoC
        internal_sram_addr = 0x40000000
        internal_sram_size = 32768
        self.soc = LunaSoC(
            cpu=MinervaCPU(
                with_debug    = False,
                with_icache   = True,
                icache_nlines = 16,
                icache_nwords = 4,
                icache_nways  = 1,
                icache_base   = internal_sram_addr,
                icache_limit  = internal_sram_addr + internal_sram_size,
                with_dcache   = True,
                dcache_nlines = 16,
                dcache_nwords = 4,
                dcache_nways  = 1,
                dcache_base   = internal_sram_addr,
                dcache_limit  = internal_sram_addr + internal_sram_size,
                with_muldiv   = False,
                reset_address = 0x00000000,
            ),
            clock_frequency=clock_frequency,
            internal_sram_addr=internal_sram_addr,
            internal_sram_size=internal_sram_size,
        )

        # ... add bios and core peripherals ...
        self.soc.add_bios_and_peripherals(uart_pins=self.uart_pins)

        # ... add our LED peripheral, for simple output.
        self.leds = LedPeripheral()
        self.soc.add_peripheral(self.leds, addr=0xf0001000)

    def elaborate(self, platform):
        m = Module()
        m.submodules.soc = self.soc

        # generate our domain clocks/resets
        m.submodules.car = platform.clock_domain_generator(clock_frequencies=CLOCK_FREQUENCIES_MHZ)

        # connect up our UART
        uart_io = platform.request("uart", 0)
        m.d.comb += [
            uart_io.tx.o.eq(self.uart_pins.tx),
            self.uart_pins.rx.eq(uart_io.rx)
        ]
        if hasattr(uart_io.tx, 'oe'):
            m.d.comb += uart_io.tx.oe.eq(~self.soc.uart._phy.tx.rdy),

        return m


# - main ----------------------------------------------------------------------

from luna.gateware.platform import get_appropriate_platform

from luna_soc.generate      import Generate, Introspect

if __name__ == "__main__":
    # disable UnusedElaborable warnings
    from amaranth._unused import MustUse
    MustUse._MustUse__silence = True

    build_dir = os.path.join("build")

    # configure logging
    configure_default_logging()
    logging.getLogger().setLevel(logging.DEBUG)

    # select platform
    platform = get_appropriate_platform()
    if platform is None:
        logging.error("Failed to identify a supported platform")
        sys.exit(1)

    # configure clock frequency
    clock_frequency = int(platform.default_clk_frequency)
    logging.info(f"Platform clock frequency: {clock_frequency}")

    # create design
    design = HelloSoc(clock_frequency=clock_frequency)

    # TODO fix litex build
    thirdparty = os.path.join(build_dir, "lambdasoc.soc.cpu/bios/3rdparty/litex")
    if not os.path.exists(thirdparty):
        logging.info("Fixing build, creating output directory: {}".format(thirdparty))
        os.makedirs(thirdparty)

    # build litex bios
    logging.info("Building bios")
    design.soc.build(name="soc",
                     build_dir=build_dir,
                     do_init=True)

    # build soc
    logging.info("Building soc")
    overrides = {
        "debug_verilog": True,
        "verbose": False,
    }
    products = platform.build(design, do_program=False, build_dir=build_dir, **overrides)

    # log resources and prepare to generate artifacts
    Introspect(design.soc).log_resources()
    generate = Generate(design.soc)

    # generate: c-header and ld-script
    path = os.path.join(build_dir, "genc")
    if not os.path.exists(path):
        os.makedirs(path)

    logging.info("Generating c-header and ld-script: {}".format(path))
    with open(os.path.join(path, "resources.h"), "w") as f:
        generate.c_header(platform_name=platform.name, file=f)
    with open(os.path.join(path, "soc.ld"), "w") as f:
        generate.ld_script(file=f)

    print("Build completed. Use 'make load' to load bitstream to device.")

    # TODO
    #top_level_cli(design)
