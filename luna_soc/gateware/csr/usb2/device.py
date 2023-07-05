#
# This file is part of LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause
"""
Contains the organizing hardware used to add USB Device functionality
to your own designs; including the core :class:`USBDevice` class.
"""

import logging

from amaranth                      import Signal, Module, Elaboratable, Const

from luna                          import configure_default_logging
from luna.gateware.usb.usb2.device import USBDevice

from ..base import Peripheral

class USBDeviceController(Peripheral, Elaboratable):
    """ SoC controller for a USBDevice.

    Breaks our USBDevice control and status signals out into registers so a CPU / Wishbone master
    can control our USB device.

    The attributes below are intended to connect to a USBDevice. Typically, they'd be created by
    using the .controller() method on a USBDevice object, which will automatically connect all
    relevant signals.

    Attributes
    ----------

    connect: Signal(), output
        High when the USBDevice should be allowed to connect to a host.

    """

    def __init__(self):
        super().__init__()

        #
        # I/O port
        #
        self.connect   = Signal(reset=1)
        self.bus_reset = Signal()


        #
        # Registers.
        #

        regs = self.csr_bank()
        self._connect = regs.csr(1, "rw", desc="""
            Set this bit to '1' to allow the associated USB device to connect to a host.
        """)

        self._speed = regs.csr(2, "r", desc="""
            Indicates the current speed of the USB device. 0 indicates High; 1 => Full,
            2 => Low, and 3 => SuperSpeed (incl SuperSpeed+).
        """)

        self._reset_irq = self.event(mode="rise", name="reset", desc="""
            Interrupt that occurs when a USB bus reset is received.
        """)

        # Wishbone connection.
        self._bridge    = self.bridge(data_width=32, granularity=8, alignment=2)
        self.bus        = self._bridge.bus
        self.irq        = self._bridge.irq


    def attach(self, device: USBDevice):
        """ Returns a list of statements necessary to connect this to a USB controller.

        The returned values makes all of the connections necessary to provide control and fetch status
        from the relevant USB device. These can be made either combinationally or synchronously, but
        combinational is recommended; as these signals are typically fed from a register anyway.

        Parameters
        ----------
        device: USBDevice
            The :class:`USBDevice` object to be controlled.
        """
        return [
            device.connect      .eq(self.connect),
            self.bus_reset      .eq(device.reset_detected),
            self._speed.r_data  .eq(device.speed)
        ]


    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = self._bridge

        # Core connection register.
        m.d.comb += self.connect.eq(self._connect.r_data)
        with m.If(self._connect.w_stb):
            m.d.usb += self._connect.r_data.eq(self._connect.w_data)

        # Reset-detection event.
        m.d.comb += self._reset_irq.stb.eq(self.bus_reset)

        return m
