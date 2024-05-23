#
# This file is part of LUNA.
#
# Copyright (c) 2024 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

# Based on code from LiteSPI

from amaranth                           import Signal, Elaboratable, Module, Cat, C, Instance, DomainRenamer
from amaranth.utils                     import bits_for, log2_int

from luna.gateware.stream               import StreamInterface

from ..vendor.amaranth_soc              import wishbone
from ..vendor.amaranth_soc.memory       import MemoryMap

from ..vendor.lambdasoc.periph          import Peripheral


__all__ = ["ECP5ConfigurationFlashInterface", "WishboneSPIFlashReader"]

class WishboneSPIFlashReader(Peripheral, Elaboratable):
    """Wishbone Memory-mapped SPI Flash controller.

    Supports sequential accesses so that command and address is only sent when necessary.
    """

    MMAP_DEFAULT_TIMEOUT = 256
    OE_MASK = {
        1: 0b00000001,
        2: 0b00000011,
        4: 0b00001111,
        8: 0b11111111,
    }

    def __init__(self, *, pads, size, data_width=32, granularity=8, name=None, domain="sync", byteorder="little"):
        super().__init__()

        self._name     = name
        self._size     = size
        self._domain   = domain
        self.pads      = pads
        self.byteorder = byteorder

        mem_depth      = (self._size * granularity) // data_width
        wb_addr_width  = log2_int(mem_depth)
        wb_data_width  = data_width
        mm_addr_width  = log2_int(self._size)
        mm_data_width  = granularity

        self.bus = wishbone.Interface(
            addr_width=wb_addr_width,
            data_width=wb_data_width,
            granularity=granularity,
        )

        map = MemoryMap(addr_width=mm_addr_width, data_width=mm_data_width, name=self._name)
        map.add_resource(self, name=self._name, size=self._size)
        self.bus.memory_map = map

    @staticmethod
    def reverse_bytes(word):
        nbytes = len(word) // 8
        return Cat(word.word_select(nbytes - i - 1, 8) for i in range(nbytes))

    def elaborate(self, platform):
        m = Module()

        # Flash configuration
        flash_read_opcode = 0xeb
        flash_cmd_bits    = 8
        flash_addr_bits   = 24
        flash_data_bits   = 32
        flash_cmd_width   = 1
        flash_addr_width  = 4
        flash_bus_width   = 4
        flash_dummy_bits  = 24
        flash_dummy_value = 0xff0000

        # Chip select
        cs = Signal()

        # PHY controller
        spi_phy = SPIPHYController(self.pads, domain=self._domain)
        m.submodules.spi_phy = spi_phy
        m.d.sync += spi_phy.cs.eq(cs)

        # Burst Control.
        burst_cs      = Signal()
        burst_adr     = Signal(len(self.bus.adr), reset_less=True)
        burst_timeout = WaitTimer(self.MMAP_DEFAULT_TIMEOUT, domain=self._domain)
        m.submodules.burst_timeout = burst_timeout

        bus    = self.bus
        source = spi_phy.sink
        sink   = spi_phy.source


        with m.FSM(domain=self._domain):
            with m.State("IDLE"):
                # Keep CS active after Burst for Timeout.
                m.d.comb += [
                    burst_timeout.wait.eq(1),
                    cs.eq(burst_cs),
                ]
                m.d.sync += burst_cs.eq(burst_cs & ~burst_timeout.done)
                # On Bus Read access...
                with m.If(bus.cyc & bus.stb & ~bus.we):
                    # If CS is still active and Bus address matches previous Burst address:
                    # Just continue the current Burst.
                    with m.If(burst_cs & (bus.adr == burst_adr)):
                        m.next = "BURST-REQ"
                    # Otherwise initialize a new Burst.
                    with m.Else():
                        m.d.comb += cs.eq(0)
                        m.next = "BURST-CMD"

            with m.State("BURST-CMD"):
                m.d.comb += [
                    cs              .eq(1),
                    source.valid    .eq(1),
                    source.data     .eq(flash_read_opcode), # send command.
                    source.len      .eq(flash_cmd_bits),
                    source.width    .eq(flash_cmd_width),
                    source.mask     .eq(self.OE_MASK[flash_cmd_width]),
                ]
                with m.If(source.ready):
                    m.next = "CMD-RET"

            with m.State("CMD-RET"):
                m.d.comb += [
                    cs              .eq(1),
                    sink.ready      .eq(1),
                ]
                with m.If(sink.valid):
                    m.next = "BURST-ADDR"

            with m.State("BURST-ADDR"):
                m.d.comb += [
                    cs              .eq(1),
                    source.valid    .eq(1),
                    source.width    .eq(flash_addr_width),
                    source.mask     .eq(self.OE_MASK[flash_addr_width]),
                    source.data     .eq(Cat(C(0, 2), bus.adr)), # send address.
                    source.len      .eq(flash_addr_bits),
                ]
                m.d.sync += [
                    burst_cs        .eq(1),
                    burst_adr       .eq(bus.adr),
                ]
                with m.If(source.ready):
                    m.next = "ADDR-RET"

            with m.State("ADDR-RET"):
                m.d.comb += [
                    cs              .eq(1),
                    sink.ready      .eq(1),
                ]
                with m.If(sink.valid):
                    with m.If(flash_dummy_bits == 0):
                        m.next = "BURST-REQ"
                    with m.Else():
                        m.next = "DUMMY"

            with m.State("DUMMY"):
                m.d.comb += [
                    cs              .eq(1),
                    source.valid    .eq(1),
                    source.width    .eq(flash_addr_width),
                    source.mask     .eq(self.OE_MASK[flash_addr_width]),
                    source.data     .eq(flash_dummy_value),
                    source.len      .eq(flash_dummy_bits),
                ]
                with m.If(source.ready):
                    m.next = "DUMMY-RET"

            with m.State("DUMMY-RET"):
                m.d.comb += [
                    cs              .eq(1),
                    sink.ready      .eq(1),
                ]
                with m.If(sink.valid):
                    m.next = "BURST-REQ"

            with m.State("BURST-REQ"):
                m.d.comb += [
                    cs              .eq(1),
                    source.valid    .eq(1),
                    source.last     .eq(1),
                    source.width    .eq(flash_bus_width),
                    source.mask     .eq(0),
                    source.len      .eq(flash_data_bits),
                ]
                with m.If(source.ready):
                    m.next = "BURST-DAT"

            with m.State("BURST-DAT"):
                word = self.reverse_bytes(sink.data) if self.byteorder == "little" else sink.data
                m.d.comb += [
                    cs              .eq(1),
                    sink.ready      .eq(1),
                    bus.dat_r       .eq(word),
                ]
                with m.If(sink.valid):
                    m.d.comb += bus.ack.eq(1)
                    m.d.sync += burst_adr.eq(burst_adr + 1)
                    m.next = "IDLE"


        # Convert our sync domain to the domain requested by the user, if necessary.
        if self._domain != "sync":
            m = DomainRenamer({"sync": self._domain})(m)

        return m


class SPIPHYController(Elaboratable):
    """Provides a generic PHY that can be used by a SPI flash controller.

    It supports single/dual/quad/octal output reads from the flash chips.
    """
    def __init__(self, pads, divisor=0, domain="sync"):
        self.divisor = divisor  # SPI frequency is clk / (2*(1+divisor))
        self.pads    = pads
        self._domain = domain
        self.sink    = StreamInterface(payload_width=32, extra_fields=[
            ("len",   6),
            ("width", 4),
            ("mask",  8),
        ])
        self.source  = StreamInterface(payload_width=32)
        self.cs      = Signal()

    def elaborate(self, platform):
        m = Module()

        pads   = self.pads
        sink   = self.sink
        source = self.source

        # Clock Generator.
        m.submodules.clkgen = clkgen = SPIClockGenerator(self.divisor, domain=self._domain)
        spi_clk_divisor = self.divisor

        # CS control: ensure cs_delay cycles between XFers.
        cs_delay = 0
        cs_enable = Signal()
        if cs_delay > 0:
            m.submodules.cs_timer = cs_timer  = WaitTimer(cs_delay + 1, domain=self._domain)
            m.d.comb += [
                cs_timer.wait    .eq(self.cs),
                cs_enable        .eq(cs_timer.done),
            ]
        else:
            m.d.comb += cs_enable.eq(self.cs)

        # I/Os.
        dq_o  = Signal.like(pads.dq.o)
        dq_i  = Signal.like(pads.dq.i)
        dq_oe = Signal.like(pads.dq.oe)
        m.d.sync += [
            pads.sck    .eq(clkgen.clk),
            pads.cs.o   .eq(cs_enable),
            pads.dq.o   .eq(dq_o),
            pads.dq.oe  .eq(dq_oe),
            dq_i        .eq(pads.dq.i),
        ]
        if hasattr(pads.cs, 'oe'):
            m.d.comb += pads.cs.oe.eq(1)

        # Data Shift Registers.
        sr_cnt       = Signal(8, reset_less=True)
        sr_out_load  = Signal()
        sr_out_shift = Signal()
        sr_out       = Signal(len(sink.data), reset_less=True)
        sr_in_shift  = Signal()
        sr_in        = Signal(len(sink.data), reset_less=True)

        # Data Out Generation/Load/Shift.
        m.d.comb += dq_oe.eq(sink.mask)
        with m.Switch(sink.width):
            with m.Case(1):
                m.d.comb += dq_o.eq(sr_out[-1:])
            with m.Case(2):
                m.d.comb += dq_o.eq(sr_out[-2:])
            with m.Case(4):
                m.d.comb += dq_o.eq(sr_out[-4:])
            with m.Case(8):
                m.d.comb += dq_o.eq(sr_out[-8:])

        with m.If(sr_out_load):
            m.d.sync += sr_out.eq(sink.data << (len(sink.data) - sink.len).as_unsigned())

        with m.If(sr_out_shift):
            with m.Switch(sink.width):
                with m.Case(1):
                    m.d.sync += sr_out.eq(Cat(C(0, 1), sr_out))
                with m.Case(2):
                    m.d.sync += sr_out.eq(Cat(C(0, 2), sr_out))
                with m.Case(4):
                    m.d.sync += sr_out.eq(Cat(C(0, 4), sr_out))
                with m.Case(8):
                    m.d.sync += sr_out.eq(Cat(C(0, 8), sr_out))

        # Data In Shift.
        with m.If(sr_in_shift):
            with m.Switch(sink.width):
                with m.Case(1):
                    m.d.sync += sr_in.eq(Cat(dq_i[1], sr_in))  # 1 = peripheral output
                with m.Case(2):
                    m.d.sync += sr_in.eq(Cat(dq_i[:2], sr_in))
                with m.Case(4):
                    m.d.sync += sr_in.eq(Cat(dq_i[:4], sr_in))
                with m.Case(8):
                    m.d.sync += sr_in.eq(Cat(dq_i[:8], sr_in))


        m.d.comb += source.data.eq(sr_in)

        with m.FSM(domain=self._domain):

            with m.State("WAIT-CMD-DATA"):
                # Wait for CS and a CMD from the Core.
                with m.If(cs_enable & sink.valid):
                    # Load Shift Register Count/Data Out.
                    m.d.sync += sr_cnt.eq(sink.len - sink.width)
                    m.d.comb += sr_out_load.eq(1)
                    # Start XFER.
                    m.next = 'XFER'

            with m.State('XFER'):
                m.d.comb += [
                    clkgen.en   .eq(1),
                    # Data in / out shift.
                    sr_in_shift .eq(clkgen.sample),
                    sr_out_shift.eq(clkgen.update),
                ]

                # Shift register count update/check.
                with m.If(clkgen.update):
                    m.d.sync += sr_cnt.eq(sr_cnt - sink.width)
                    # End xfer.
                    with m.If(sr_cnt == 0):
                        m.next = 'XFER-END'

            with m.State('XFER-END'):
                # Last data already captured in XFER when divisor > 0 so only capture for divisor == 0.
                with m.If((spi_clk_divisor > 0) | clkgen.sample):
                    # Accept CMD.
                    m.d.comb += sink.ready.eq(1)
                    # Capture last data (only for spi_clk_divisor == 0).
                    m.d.comb += sr_in_shift.eq(spi_clk_divisor == 0)
                    # Send Status/Data to Core.
                    m.next = "SEND-STATUS-DATA"

            with m.State('SEND-STATUS-DATA'):
                # Send data in to core and return to IDLE when accepted.
                m.d.comb += source.valid.eq(1)
                m.d.comb += source.last .eq(1)
                with m.If(source.ready):
                    m.next = 'WAIT-CMD-DATA'

        # Convert our sync domain to the domain requested by the user, if necessary.
        if self._domain != "sync":
            m = DomainRenamer({"sync": self._domain})(m)

        return m



class SPIClockGenerator(Elaboratable):
    def __init__(self, divisor, domain="sync"):
        self._domain      = domain
        self.div          = divisor
        self.en           = Signal()
        self.clk          = Signal()
        self.sample       = Signal()
        self.update       = Signal()

    def elaborate(self, platform):
        m = Module()

        div          = self.div
        cnt_width    = bits_for(div)
        cnt          = Signal(cnt_width)
        posedge      = Signal()
        negedge      = Signal()
        posedge_reg  = Signal()
        posedge_reg2 = Signal()

        m.d.comb += [
            posedge     .eq(self.en & ~self.clk & (cnt == div)),
            negedge     .eq(self.en &  self.clk & (cnt == div)),
            self.update .eq(negedge),
            self.sample .eq(posedge_reg2),
        ]

        # Delayed edge to account for IO register delays.
        m.d.sync += [
            posedge_reg    .eq(posedge),
            posedge_reg2   .eq(posedge_reg),
        ]

        with m.If(self.en):
            with m.If(cnt < div):
                m.d.sync += cnt.eq(cnt + 1)
            with m.Else():
                m.d.sync += [
                    cnt.eq(0),
                    self.clk.eq(~self.clk),
                ]
        with m.Else():
            m.d.sync += [
                cnt.eq(0),
                self.clk.eq(0),
            ]

        # Convert our sync domain to the domain requested by the user, if necessary.
        if self._domain != "sync":
            m = DomainRenamer({"sync": self._domain})(m)

        return m


class WaitTimer(Elaboratable):
    def __init__(self, t, domain="sync"):
        self._domain = domain
        self.t    = t
        self.wait = Signal()
        self.done = Signal()

    def elaborate(self, platform):
        m = Module()

        t     = int(self.t)
        count = Signal(bits_for(t), reset=t)

        m.d.comb += self.done.eq(count == 0)
        with m.If(self.wait):
            with m.If(~self.done):
                m.d.sync += count.eq(count - 1)
        with m.Else():
            m.d.sync += count.eq(count.reset)

        # Convert our sync domain to the domain requested by the user, if necessary.
        if self._domain != "sync":
            m = DomainRenamer({"sync": self._domain})(m)

        return m



class ECP5ConfigurationFlashInterface(Elaboratable):
    """ Gateware that creates a connection to an MSPI configuration flash.

    Automatically uses appropriate platform resources; this abstracts away details
    necessary to e.g. drive the MCLK lines on an ECP5, which has special handling.
    """
    def __init__(self, *, bus):
        """ Params:
            bus    -- The SPI bus object to extend.
        """
        self.bus    = bus
        self.sck    = Signal()

    def __getattr__(self, name):
        try:
            return getattr(self.bus, name)
        except IndexError:
            return object.__getattribute__(self, name)

    def elaborate(self, platform):
        m = Module()

        # Get the ECP5 block that's responsible for driving the MCLK pin,
        # and drive it using our SCK line.
        user_mclk = Instance('USRMCLK', i_USRMCLKI=self.sck, i_USRMCLKTS=0)
        m.submodules += user_mclk

        return m
