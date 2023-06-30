#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

from amaranth         import Cat, Elaboratable, Module, Signal, Record
from lambdasoc.periph import Peripheral

class LedPeripheral(Peripheral, Elaboratable):
    """ Example peripheral that controls the board's LEDs. """

    def __init__(self, name="leds"):
        super().__init__(name=name)

        # Create our LED register.
        # Note that there's a bunch of 'magic' that goes on behind the scenes, here:
        # a memory address will automatically be reserved for this register in the address
        # space it's attached to; and the SoC utilities will automatically generate header
        # entires and stub functions for it.
        bank            = self.csr_bank()
        self._output    = bank.csr(6, "w")

        # ... and convert our register into a Wishbone peripheral.
        self._bridge    = self.bridge(data_width=32, granularity=8, alignment=2)
        self.bus        = self._bridge.bus


    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = self._bridge

        # Grab our LEDS...
        leds = Cat(platform.request("led", i) for i in range(6))

        # ... and update them on each register write.
        with m.If(self._output.w_stb):
            m.d.sync += leds.eq(self._output.w_data)

        return m
