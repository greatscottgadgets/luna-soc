#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

"""VexRiscv SoC for LUNA firmware."""

from .cpu.vexriscv     import VexRiscv
from .csr.sram         import SRAMPeripheral as SRAMPeripheralWithACK
from .wishbone.memory  import WishboneRAM, WishboneROM
from ..generate        import Introspect

from amaranth                import *
from amaranth.build          import *

import amaranth_soc
from amaranth_soc            import wishbone
from amaranth_soc.periph     import ConstantMap
from amaranth_stdio.serial   import AsyncSerial

import lambdasoc
from lambdasoc.cpu.minerva   import MinervaCPU
from lambdasoc.periph.intc   import GenericInterruptController
from lambdasoc.periph.serial import AsyncSerialPeripheral
from lambdasoc.periph.sram   import SRAMPeripheral
from lambdasoc.periph.timer  import TimerPeripheral
from lambdasoc.soc.cpu       import CPUSoC, BIOSBuilder

from lambdasoc.sim.platform          import CXXRTLPlatform
from lambdasoc.sim.blackboxes.serial import AsyncSerial_Blackbox

import logging


# - CoreSoC -------------------------------------------------------------------

class CoreSoC(CPUSoC, Elaboratable):
    # TODO lose internal_sram_addr and internal_sram_size
    def __init__(self, cpu=MinervaCPU(), clock_frequency=int(60e6), internal_sram_addr=0x40000000, internal_sram_size=int(32768), with_debug=False):
        super().__init__()

        self.internal_sram_addr = internal_sram_addr
        self.internal_sram_size = internal_sram_size

        # create system bus
        self._bus_arbiter = wishbone.Arbiter(addr_width=30, data_width=32, granularity=8,
                                             features={"cti", "bte", "err"})
        self._bus_decoder = wishbone.Decoder(addr_width=30, data_width=32, granularity=8,
                                             alignment=0,
                                             features={"cti", "bte", "err"})
        self._bus_arbiter.add(cpu.ibus)
        self._bus_arbiter.add(cpu.dbus)

        # create interrupt controller
        if isinstance(cpu, MinervaCPU):
            self.cpu_irq_external = cpu.ip
        elif isinstance(cpu, VexRiscv):
            self.cpu_irq_external = cpu.irq_external
        else:
            raise ValueError(f"Unsupported CPU: {cpu}")
        intc = GenericInterruptController(width=len(self.cpu_irq_external))

        # assign CPUSoC socproperties
        self.sync_clk_freq = clock_frequency
        self.cpu = cpu
        self.intc = intc

        # Things we don't have but lambdasoc's jinja2 templates expect
        # TODO should we just make them properties?
        self.mainram = None
        self.sdram = None
        self.ethmac = None

        # random state it would be nice to get rid of
        self._interrupt_index = 0
        self._interrupt_map = {}
        self._peripherals = []
        self._has_bios = False


    # - CoreSoC @properties --

    @property
    def has_bios(self):
        return self._has_bios

    # - CPUSoC @property overrides --

    @property
    def constants(self):
        return super().constants.union(
            #SDRAM  = self.sdram .constant_map if self.sdram  is not None else None,
            #ETHMAC = self.ethmac.constant_map if self.ethmac is not None else None,
            SOC = ConstantMap(
                #WITH_SDRAM        = self.sdram  is not None,
                #WITH_ETHMAC       = self.ethmac is not None,
                MEMTEST_ADDR_SIZE = self.internal_sram_size,
                MEMTEST_DATA_SIZE = self.internal_sram_size,
            ),
        )

    @property
    def memory_map(self):
        return self._bus_decoder.bus.memory_map

    # - Elaboratable --

    def elaborate(self, platform):
        m = Module()

        m.submodules.cpu        = self.cpu
        m.submodules.arbiter    = self._bus_arbiter
        m.submodules.decoder    = self._bus_decoder
        m.submodules.intc       = self.intc

        for peripheral in self._peripherals:
            m.submodules += peripheral

        m.d.comb += [
            self._bus_arbiter.bus.connect(self._bus_decoder.bus),
            self.cpu_irq_external.eq(self.intc.ip),
        ]

        return m


# - LunaSoC -------------------------------------------------------------------

class LunaSoC(CoreSoC):
    """ Class used for building simple system-on-a-chip architectures.

    Intended to facilitate custom SoC designs by providing  a wrapper that
    can be updated as the Amaranth-based-SoC landscape changes. Hopefully,
    this will eventually be filled by e.g. Amaranth-compatible-LiteX. :)

    LUNA-SOC devices integrate:
        - A RiscV processor.
        - One or more read-only or read-write memories.
        - A number of amaranth-soc peripherals.

    The current implementation uses a single, 32-bit wide Wishbone bus
    as the system's backend; and uses lambdasoc as its backing technology.
    This is subject to change.
    """

    # - LunaSoC user api --

    # TODO move internal_sram_addr and internal_sram_size here
    def add_bios_and_peripherals(self, uart_pins, uart_baud_rate=115200, fixed_addresses=False):
        """ Adds a simple BIOS that allows loading firmware, and the requisite peripherals.

        Automatically adds the following peripherals:
            self.bootrom        -- A ROM memory used for the BIOS. (required by LambdaSoC)
            self.scratchpad     -- A RAM memory used for the BIOS. (required by LambdaSoC)
            self.uart           -- An AsyncSerialPeripheral used for serial I/O.
            self.timer          -- A TimerPeripheral used for BIOS timing.
            self.mainram        -- Program RAM.

        Parameters:
            uart_pins       -- The UARTResource to be used for UART communications; or an equivalent record.
            uart_baud_rate  -- The baud rate to be used by the BIOS' uart.
        """

        # memory configuration
        bootrom_addr       = 0x00000000
        bootrom_size       = 0x4000
        scratchpad_addr    = 0x10000000
        scratchpad_size    = 0x1000
        internal_sram_size = self.internal_sram_size
        internal_sram_addr = self.internal_sram_addr

        # timer configuration
        timer_addr  = 0xf0000100
        timer_width = 32
        timer_irqno = self._interrupt_index
        self._interrupt_index += 1

        # uart configuration
        uart_addr  = 0xf0000200
        uart_irqno = self._interrupt_index
        self._interrupt_index += 1
        uart_core = AsyncSerial(
            data_bits = 8,
            divisor   = int(self.sync_clk_freq // uart_baud_rate),
            pins      = uart_pins,
        )

        # add bootrom, scratchpad, uart, timer, mainram
        self.bootrom = SRAMPeripheral(size=bootrom_size, writable=False)
        self._bus_decoder.add(self.bootrom.bus, addr=bootrom_addr)

        self.scratchpad = SRAMPeripheral(size=scratchpad_size)
        self._bus_decoder.add(self.scratchpad.bus, addr=scratchpad_addr)

        # VexRiscv does not like LambdaSoC RAM for main program memory
        self.mainram = SRAMPeripheralWithACK(size=internal_sram_size)
        # self.mainram = WishboneRAM(
        #     name = "internal_sram",
        #     addr_width = (self.internal_sram_size - 1).bit_length(),
        # )
        self._bus_decoder.add(self.mainram.bus, addr=internal_sram_addr)

        self.timer = TimerPeripheral(width=timer_width)
        self._bus_decoder.add(self.timer.bus, addr=timer_addr)
        self.intc.add_irq(self.timer.irq, index=timer_irqno)
        self._interrupt_map[timer_irqno] = self.timer

        self.uart = AsyncSerialPeripheral(core=uart_core)
        self._bus_decoder.add(self.uart.bus, addr=uart_addr)
        self.intc.add_irq(self.uart.irq, index=uart_irqno)
        self._interrupt_map[uart_irqno] = self.uart

        # Set a hint for top_level_cli to perform a bios build.
        self._bios = True

    def add_peripheral(self, peripheral: lambdasoc.periph.Peripheral, *, as_submodule=True, **kwargs) -> lambdasoc.periph.Peripheral:
        """Helper function to add a peripheral to the SoC.

        This is identical to adding a peripheral to the SoC's wishbone
        bus and adding any visible interrupt line to the interrupt
        controller.

        Returns the peripheral provided.
        """
        if not hasattr(peripheral, "bus"):
            raise AttributeError(f"Peripheral '{peripheral}' has no bus interface.");

        self._bus_decoder.add(peripheral.bus, **kwargs)

        try:
            peripheral_irq = getattr(peripheral, "irq")
            index = self._interrupt_index

            self.intc.add_irq(peripheral_irq, index)
            self._interrupt_map[index] = peripheral

            self._interrupt_index += 1
        except (AttributeError, NotImplementedError):
            # If the object has no associated IRQs, continue anyway.
            # This allows us to add devices with only Wishbone interfaces to our SoC.
            pass

        if as_submodule:
            self._peripherals.append(peripheral)

        return peripheral

    # - Elaboratable --

    def elaborate(self, platform):
        m = super().elaborate(platform)

        m.submodules.uart       = self.uart
        m.submodules.timer      = self.timer
        m.submodules.bootrom    = self.bootrom
        m.submodules.scratchpad = self.scratchpad

        if self.mainram is not None:
            m.submodules.mainram = self.mainram

        return m


    # - LambdaSoC build --

    def build(self, name=None, build_dir="build", do_build=True, do_init=True):
        """ Builds any internal artifacts necessary to create our CPU.

        This is usually used for e.g. building our BIOS.

        Parmeters:
            name      -- The name for the SoC design.
            build_dir -- The directory where our main Amaranth build is being performed.
                         We'll build in a subdirectory of it.
        """

        super().build(build_dir=build_dir, name=name, do_build=do_build, do_init=do_init)


    # - integration API -- TODO remove these entirely and call Introspect directly from generate/gen*

    def resources(self, omit_bios_mem=True):
        return Introspect(self).resources(omit_bios_mem)

    def range_for_peripheral(self, target_peripheral: lambdasoc.periph.Peripheral):
        return Introspect(self).range_for_peripheral(target_peripheral)

    def irq_for_peripheral_window(self, target_peripheral_window: amaranth_soc.memory.MemoryMap):
        return Introspect(self).irq_for_peripheral_window(target_peripheral_window)
