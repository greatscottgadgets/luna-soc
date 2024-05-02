#
# This file is part of LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

import logging
import os
import sys

from luna                            import configure_default_logging
from luna.gateware.usb.usb2.device   import USBDevice

from amaranth                        import Elaboratable, Module, Cat
from amaranth.hdl.rec                import Record

from luna_soc.gateware.cpu.minerva   import Minerva
from luna_soc.gateware.csr           import GpioPeripheral, LedPeripheral
from luna_soc.gateware.lunasoc       import LunaSoC

from luna_soc.util.readbin           import get_mem_data


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
            cpu=Minerva(
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
                reset_address = internal_sram_addr,
            ),
            clock_frequency=clock_frequency,
        )

        # ... read our firmware binary ...
        firmware = get_mem_data("firmware.bin", data_width=32, endianness="little")

        # ... add core peripherals: memory, timer, uart ...
        self.soc.add_core_peripherals(
            uart_pins=self.uart_pins,
            internal_sram_addr=internal_sram_addr,
            internal_sram_size=internal_sram_size,
            internal_sram_init=firmware,
        )

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

if __name__ == "__main__":
    from luna_soc import top_level_cli

    design = HelloSoc(clock_frequency=int(60e6))
    top_level_cli(design)
