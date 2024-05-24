#!/usr/bin/env python3
#
# This file is part of LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

import logging
import os
import sys

from amaranth                       import Cat, ClockSignal, Elaboratable, Module, ResetSignal
from amaranth.hdl.rec               import Record

from luna                           import configure_default_logging
from luna.gateware.interface.psram  import HyperRAMPHY, HyperRAMInterface
from luna.gateware.interface.ulpi   import ULPIRegisterWindow
from luna.gateware.usb.usb2.device  import USBDevice

from luna_soc.gateware.cpu.minerva  import Minerva
from luna_soc.gateware.csr          import GpioPeripheral, LedPeripheral, UARTPeripheral
from luna_soc.gateware.lunasoc      import LunaSoC

from luna_soc.gateware.vendor.amaranth_stdio.serial   import AsyncSerial

from luna_soc.gateware.vendor.lambdasoc.periph        import Peripheral
from luna_soc.gateware.vendor.lambdasoc.periph.serial import AsyncSerialPeripheral
from luna_soc.gateware.vendor.lambdasoc.periph.sram   import SRAMPeripheral
from luna_soc.gateware.vendor.lambdasoc.periph.timer  import TimerPeripheral

from luna_soc.util.readbin          import get_mem_data


# Run our tests at a slower clock rate, for now.
# TODO: bump up the fast clock rate, to test the HyperRAM at speed?
CLOCK_FREQUENCIES_MHZ = {
    "fast": 120,
    "sync":  60,
    "usb":   60,
}


# - ULPIRegisterPeripheral ----------------------------------------------------

class ULPIRegisterPeripheral(Peripheral, Elaboratable):
    """ Peripheral that provides access to a ULPI PHY, and its registers. """

    def __init__(self, name="ulpi", io_resource_name="usb"):
        super().__init__(name=name)
        self._io_resource = io_resource_name

        # Create our registers...
        bank            = self.csr_bank()
        self._address   = bank.csr(8, "w")
        self._value     = bank.csr(8, "rw")
        self._busy      = bank.csr(1, "r")

        # ... and convert our register into a Wishbone peripheral.
        self._bridge    = self.bridge(data_width=32, granularity=8, alignment=2)
        self.bus        = self._bridge.bus


    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = self._bridge

        # Grab a connection to our ULPI PHY.
        target_ulpi = platform.request(self._io_resource)

        #
        # ULPI Register Window
        #
        ulpi_reg_window  = ULPIRegisterWindow()
        m.submodules  += ulpi_reg_window

        # Connect up the window.
        m.d.comb += [
            ulpi_reg_window.ulpi_data_in  .eq(target_ulpi.data.i),
            ulpi_reg_window.ulpi_dir      .eq(target_ulpi.dir.i),
            ulpi_reg_window.ulpi_next     .eq(target_ulpi.nxt.i),

            target_ulpi.clk.o             .eq(ClockSignal("usb")),
            target_ulpi.rst.o             .eq(ResetSignal("usb")),
            target_ulpi.stp.o             .eq(ulpi_reg_window.ulpi_stop),
            target_ulpi.data.o            .eq(ulpi_reg_window.ulpi_data_out),
            target_ulpi.data.oe           .eq(~target_ulpi.dir.i)
        ]

        #
        # Address register logic.
        #

        # Perform a read request whenever the user writes to ULPI address...
        m.d.sync += ulpi_reg_window.read_request.eq(self._address.w_stb)

        # And update the register address accordingly.
        with m.If(self._address.w_stb):
            m.d.sync += ulpi_reg_window.address.eq(self._address.w_data)


        #
        # Value register logic.
        #

        # Always report back the last read data.
        m.d.comb += self._value.r_data.eq(ulpi_reg_window.read_data)

        # Perform a write whenever the user writes to our ULPI value.
        m.d.sync += ulpi_reg_window.write_request.eq(self._value.w_stb)
        with m.If(self._address.w_stb):
            m.d.sync += ulpi_reg_window.write_data.eq(self._value.w_data)


        #
        # Busy register logic.
        #
        m.d.comb += self._busy.r_data.eq(ulpi_reg_window.busy)

        return m


# - PSRAMRegisterPeripheral ---------------------------------------------------

class PSRAMRegisterPeripheral(Peripheral, Elaboratable):
    """ Peripheral that provides access to a ULPI PHY, and its registers. """

    def __init__(self, name="ram"):
        super().__init__(name=name)

        # Create our registers...
        bank            = self.csr_bank()
        self._address   = bank.csr(32, "w")
        self._value     = bank.csr(32, "r")
        self._busy      = bank.csr(1,  "r")

        # ... and convert our register into a Wishbone peripheral.
        self._bridge    = self.bridge(data_width=32, granularity=8, alignment=2)
        self.bus        = self._bridge.bus


    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = self._bridge

        #
        # HyperRAM interface window.
        #
        ram_bus = platform.request('ram')
        m.submodules.psram_phy = psram_phy = HyperRAMPHY(bus=ram_bus)
        m.submodules.psram = psram = HyperRAMInterface(phy=psram_phy.phy)

        # Hook up our PSRAM.
        m.d.comb += [
            ram_bus.reset.o        .eq(0),
            psram.single_page      .eq(0),
            psram.perform_write    .eq(0),
            psram.register_space   .eq(1),
            psram.final_word       .eq(1),
        ]

        #
        # Address register logic.
        #

        # Perform a read request whenever the user writes the address register...
        m.d.sync += psram.start_transfer.eq(self._address.w_stb)

        # And update the register address accordingly.
        with m.If(self._address.w_stb):
            m.d.sync += psram.address.eq(self._address.w_data)


        #
        # Value register logic.
        #

        # Always report back the last read data.
        with m.If(psram.read_ready):
            m.d.sync += self._value.r_data.eq(psram.read_data)


        #
        # Busy register logic.
        #
        m.d.comb += self._busy.r_data.eq(~psram.idle)

        return m


# - SelftestCore --------------------------------------------------------------

class SelftestCore(Elaboratable):
    def __init__(self):
        # configure clock frequency
        clock_frequency = int(CLOCK_FREQUENCIES_MHZ["sync"] * 1e6)

        # create our SoC
        self.soc = LunaSoC(
            cpu=Minerva(
                with_muldiv=True,
                with_debug=False,
                reset_address=0x00000000,
            ),
            clock_frequency=clock_frequency,
        )

        # ... read our firmware binary ...
        firmware = get_mem_data("selftest.bin", data_width=32, endianness="little")

        # ... add a ROM for firmware ...
        self.soc.bootrom = SRAMPeripheral(size=0x4000, writable=False, init=firmware)
        self.soc.add_peripheral(self.soc.bootrom, addr=0x00000000)

        # ... and a RAM for execution ...
        self.soc.scratchpad = SRAMPeripheral(size=0x4000)
        self.soc.add_peripheral(self.soc.scratchpad, addr=0x00004000)

        # ... add a timer, so our software can get precise timing ...
        self.soc.timer = TimerPeripheral(width=32)
        self.soc.add_peripheral(self.soc.timer)

        # ... add our UART peripheral ...
        self.uart_pins = Record([
            ('rx', [('i', 1)]),
            ('tx', [('o', 1)])
        ])
        self.soc.uart = AsyncSerialPeripheral(core=AsyncSerial(
            data_bits = 8,
            divisor   = int(clock_frequency // 115200),
            pins      = self.uart_pins,
        ))
        self.soc.add_peripheral(self.soc.uart)

        # ... and add our peripherals under test.
        peripherals = (
            LedPeripheral(name="leds"),
            ULPIRegisterPeripheral(name="target_ulpi",   io_resource_name="target_phy"),
            ULPIRegisterPeripheral(name="host_ulpi",     io_resource_name="control_phy"),
            ULPIRegisterPeripheral(name="sideband_ulpi", io_resource_name="aux_phy"),
            PSRAMRegisterPeripheral(name="psram"),
        )

        for peripheral in peripherals:
            self.soc.add_peripheral(peripheral)


    def elaborate(self, platform):
        m = Module()
        # generate our domain clocks/resets
        m.submodules.car = platform.clock_domain_generator(clock_frequencies=CLOCK_FREQUENCIES_MHZ)

        # add our SoC to the design
        m.submodules.soc = self.soc

        # connect up our UART
        uart_io = platform.request("uart", 0)
        m.d.comb += [
            uart_io.tx.o.eq(self.uart_pins.tx),
            self.uart_pins.rx.eq(uart_io.rx)
        ]
        if hasattr(uart_io.tx, 'oe'):
            m.d.comb += uart_io.tx.oe.eq(~self.soc.uart._phy.tx.rdy)

        return m


# - main ----------------------------------------------------------------------

if __name__ == "__main__":
    from luna_soc import top_level_cli

    design = SelftestCore()
    top_level_cli(design)
