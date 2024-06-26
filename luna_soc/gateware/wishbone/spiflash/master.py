#
# This file is part of LUNA.
#
# Copyright (c) 2024 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

# Based on code from LiteSPI

from amaranth                           import Module, DomainRenamer, Signal
from amaranth.lib                       import wiring
from amaranth.lib.fifo                  import SyncFIFO
from amaranth.lib.data                  import StructLayout, View

from ...vendor.lambdasoc.periph         import Peripheral

from .port                              import SPIControlPort


class SPIFlashMaster(Peripheral, wiring.Component):
    """Wishbone generic SPI Flash master.

    Provides a generic SPI master that can be controlled using CSRs.
    Supports multiple access modes with the help of ``width`` and ``mask`` registers which
    can be used to configure the PHY into any supported SDR mode (single/dual/quad/octal).
    """
    def __init__(self, *, data_width=32, granularity=8, rx_depth=16, tx_depth=16, name=None, domain="sync"):
        wiring.Component.__init__(self, SPIControlPort(data_width))
        Peripheral.__init__(self)

        self._domain   = domain

        # Layout description for writing to the TX FIFO.
        self.tx_fifo_layout = StructLayout({
            "data":  len(self.source.data),
            "len":   len(self.source.len),
            "width": len(self.source.width),
            "mask":  len(self.source.mask),
        })

        # FIFOs.
        self._rx_fifo = DomainRenamer(domain)(SyncFIFO(width=len(self.sink.payload), depth=rx_depth))
        self._tx_fifo = DomainRenamer(domain)(SyncFIFO(width=len(self.source.payload), depth=tx_depth))

        # CSRs.
        self.bank = bank = self.csr_bank()

        self._phy_len   = bank.csr(len(self.source.len), "rw")    # SPI transfer length in bits.
        self._phy_width = bank.csr(len(self.source.width), "rw")  # SPI transfer bus width (1/2/4/8).
        self._phy_mask  = bank.csr(len(self.source.mask), "rw")   # SPI DQ output enable mask.
        self._cs        = bank.csr(1, "rw")                       # SPI chip select signal.

        self._rxtx      = bank.csr(data_width, "rw")              # Read/Write register, connected to FIFOs.

        self._tx_rdy    = bank.csr(1, "r")                        # TX FIFO ready to be written.
        self._rx_rdy    = bank.csr(1, "r")                        # RX FIFO contains data.

        # Create Wishbone bridge.
        self._bridge    = self.bridge(data_width=data_width, granularity=granularity)
        self.bus        = self._bridge.bus


    def elaborate(self, platform):
        m = Module()

        # Wishbone-CSR bridge.
        m.submodules.bridge = self._bridge

        # FIFOs.
        m.submodules.rx_fifo = rx_fifo = self._rx_fifo
        m.submodules.tx_fifo = tx_fifo = self._tx_fifo

        # Register values for a set of CSRs.
        for reg in [self._phy_len, self._phy_mask, self._phy_width, self._cs]:
            with m.If(reg.w_stb):
                m.d.sync += reg.r_data.eq(reg.w_data)

        # Chip select generation.
        cs = Signal()
        with m.FSM():
            with m.State("RISE"):
                # Enable chip select when the CSR is set to 1 and the TX FIFO contains something.
                m.d.comb += cs.eq(tx_fifo.r_rdy)
                with m.If(cs == 1):
                    m.next = "FALL"
            with m.State("FALL"):
                # Only disable chip select after the current TX FIFO is emptied.
                m.d.comb += cs.eq(self._cs.r_data | tx_fifo.r_rdy)
                with m.If(cs == 0):
                    m.next = "RISE"

        # Connect FIFOs to PHY streams.
        tx_fifo_payload = View(self.tx_fifo_layout, tx_fifo.w_data)
        m.d.comb += [
            # CSRs to TX FIFO.
            tx_fifo_payload.data    .eq(self._rxtx.w_data),
            tx_fifo_payload.len     .eq(self._phy_len.r_data),
            tx_fifo_payload.width   .eq(self._phy_width.r_data),
            tx_fifo_payload.mask    .eq(self._phy_mask.r_data),
            tx_fifo.w_en            .eq(self._rxtx.w_stb),

            # SPI chip select.
            self.cs                 .eq(cs),

            # TX FIFO to SPI PHY (PICO).
            self.source.payload     .eq(tx_fifo.r_data),
            self.source.valid       .eq(tx_fifo.r_rdy),
            tx_fifo.r_en            .eq(self.source.ready),

            # SPI PHY (POCI) to RX FIFO.
            rx_fifo.w_data          .eq(self.sink.payload),
            rx_fifo.w_en            .eq(self.sink.valid),
            self.sink.ready         .eq(rx_fifo.w_rdy),

            # RX FIFO to CSRs.
            rx_fifo.r_en            .eq(self._rxtx.r_stb),
            self._rxtx.r_data       .eq(rx_fifo.r_data),

            # FIFOs ready flags.
            self._rx_rdy.r_data     .eq(rx_fifo.r_rdy),
            self._tx_rdy.r_data     .eq(tx_fifo.w_rdy),
        ]

        # Convert our sync domain to the domain requested by the user, if necessary.
        if self._domain != "sync":
            m = DomainRenamer({"sync": self._domain})(m)

        return m
