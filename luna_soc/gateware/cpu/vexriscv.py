#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

from amaranth import *
from amaranth_soc import wishbone
from amaranth_soc.periph import ConstantMap

from lambdasoc.cpu import CPU
from lambdasoc.soc.cpu import ConstantAddr

import os
import logging

# Variants --------------------------------------------------------------------

CPU_VARIANTS = {
    "cynthion":     "vexriscv_cynthion",
    "imac+dcache":  "vexriscv_imac+dcache",
    "imac+litex":   "vexriscv_imac+litex",
    "imc":          "vexriscv_imc",
}

# - VexRiscv ------------------------------------------------------------------

class VexRiscv(CPU, Elaboratable):
    name       = "vexriscv"
    arch       = "riscv"
    byteorder  = "little"
    data_width = 32

    def __init__(self,
                 variant="imac+dcache",
                 reset_addr=0x00000000):
        super().__init__()

        self._reset_addr = reset_addr

        # ports
        self.ext_reset = Signal()
        self.irq_external = Signal(32)
        self.irq_timer    = Signal()
        self.irq_software = Signal()
        self.ibus  = wishbone.Interface(addr_width=30, data_width=32, granularity=8,
                                        features={"cti", "bte", "err"})
        self.dbus  = wishbone.Interface(addr_width=30, data_width=32, granularity=8,
                                        features={"cti", "bte", "err"})

        # read source verilog
        if not variant in CPU_VARIANTS:
            raise ValueError(f"unsupported variant: {variant}")
        self._source_file = f"{CPU_VARIANTS[variant]}.v"
        self._source_path = os.path.join(os.path.dirname(__file__), "verilog", "vexriscv", self._source_file)
        if not os.path.exists(self._source_path):
            FileNotFoundError(f"Verilog source file not found: {self._source_path}")
        with open(self._source_path, "r") as f:
            logging.info(f"reading verilog file: {self._source_path}")
            self._source_verilog = f.read()

    @property
    def reset_addr(self):
        return self._reset_addr

    @property
    def muldiv(self):
        return "hard" # "hard" if self._cpu.with_muldiv else "soft"

    @property
    def constant_map(self):
        return ConstantMap(
            VEXRISCV          = True,
            RESET_ADDR        = self._reset_addr, # ConstantAddr(self._reset_addr),
            ARCH_RISCV        = True,
            RISCV_MULDIV_SOFT = self.muldiv == "soft",
            BYTEORDER_LITTLE  = True,
        )

    def elaborate(self, platform):
        m = Module()

        # signals
        i_clk       = ClockSignal("sync")
        i_reset     = ResetSignal("sync") | self.ext_reset

        # instantiate VexRiscv
        platform.add_file(self._source_file, self._source_verilog)
        self._cpu = Instance(
            "VexRiscv",
            # clock and reset
            i_clk                    = i_clk,
            i_reset                  = i_reset,
            i_externalResetVector    = Signal(32, reset=self._reset_addr),

            # interrupts
            i_externalInterruptArray = self.irq_external,
            i_timerInterrupt         = self.irq_timer,
            i_softwareInterrupt      = self.irq_software,

            # instruction bus
            o_iBusWishbone_ADR       = self.ibus.adr,
            o_iBusWishbone_DAT_MOSI  = self.ibus.dat_w,
            o_iBusWishbone_SEL       = self.ibus.sel,
            o_iBusWishbone_CYC       = self.ibus.cyc,
            o_iBusWishbone_STB       = self.ibus.stb,
            o_iBusWishbone_WE        = self.ibus.we,
            o_iBusWishbone_CTI       = self.ibus.cti,
            o_iBusWishbone_BTE       = self.ibus.bte,
            i_iBusWishbone_DAT_MISO  = self.ibus.dat_r,
            i_iBusWishbone_ACK       = self.ibus.ack,
            i_iBusWishbone_ERR       = self.ibus.err,

            # data bus
            o_dBusWishbone_ADR       = self.dbus.adr,
            o_dBusWishbone_DAT_MOSI  = self.dbus.dat_w,
            o_dBusWishbone_SEL       = self.dbus.sel,
            o_dBusWishbone_CYC       = self.dbus.cyc,
            o_dBusWishbone_STB       = self.dbus.stb,
            o_dBusWishbone_WE        = self.dbus.we,
            o_dBusWishbone_CTI       = self.dbus.cti,
            o_dBusWishbone_BTE       = self.dbus.bte,
            i_dBusWishbone_DAT_MISO  = self.dbus.dat_r,
            i_dBusWishbone_ACK       = self.dbus.ack,
            i_dBusWishbone_ERR       = self.dbus.err,
        )

        m.submodules.vexriscv = self._cpu

        return m
