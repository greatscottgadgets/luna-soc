#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

from amaranth         import Elaboratable, Module, Signal, Record
from amaranth.hdl.rec import DIR_FANIN, DIR_FANOUT

from .base import Peripheral

__all__ = ["GpioPeripheral"]

class GpioPeripheral(Peripheral, Elaboratable):
    """ GPIO peripheral. """

    def __init__(self, width=8):
        super().__init__()

        self.pins = Record([
            ("oe", width, DIR_FANOUT),
            ("o",  width, DIR_FANOUT),
            ("i",  width, DIR_FANIN),
        ])
        self.width = width

        # peripheral control registers
        regs        = self.csr_bank()
        self._moder = regs.csr(width, "rw")
        self._odr   = regs.csr(width, "w")
        self._idr   = regs.csr(width, "r")

        # peripheral events
        self._ev    = self.event(mode="rise")

        # peripheral bus
        self._bridge = self.bridge(data_width=32, granularity=8, alignment=2)
        self.bus     = self._bridge.bus
        self.irq     = self._bridge.irq


    def elaborate(self, platform):
        m = Module()

        # set pin output enable states: 0=output, 1=input
        moder = Signal(self.width)
        with m.If(self._odr.w_stb):
            m.d.sync += moder.eq(self._moder.w_data)
        m.d.comb += self.pins.oe.eq(moder)

        # set pin output states
        odr = Signal(self.width)
        with m.If(self._odr.w_stb):
            m.d.sync += odr.eq(self._odr.w_data)
        m.d.comb += self.pins.o.eq(odr)

        # get pin input states
        idr = Signal(self.width)
        m.d.comb += idr.eq(self.pins.i & moder)
        with m.If(self._idr.r_stb):
            m.d.sync += self._idr.r_data.eq(idr)

        # trigger interrupt on pin input
        m.d.comb += self._ev.stb.eq(idr.any())

        # submodules
        m.submodules.bridge = self._bridge

        return m
