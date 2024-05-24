from amaranth import *

try:
    from minerva.core import Minerva as MinervaCore
except:
    raise ImportError("To use Minerva with luna-soc you need to install it: pip install git+https://github.com/minerva-cpu/minerva")

from ..vendor.amaranth_soc import wishbone
from ..vendor.amaranth_soc.periph import ConstantMap


__all__ = ["Minerva"]


class Minerva(Elaboratable):
    name       = "minerva"
    arch       = "riscv"
    byteorder  = "little"
    data_width = 32

    def __init__(self, **kwargs):
        super().__init__()
        self._cpu = MinervaCore(**kwargs)
        self.ibus = wishbone.Interface(addr_width=30, data_width=32, granularity=8,
                                       features={"err", "cti", "bte"})
        self.dbus = wishbone.Interface(addr_width=30, data_width=32, granularity=8,
                                       features={"err", "cti", "bte"})
        self.irq_external = Signal.like(self._cpu.external_interrupt)

    @property
    def reset_addr(self):
        return self._cpu.reset_address

    @property
    def muldiv(self):
        return "hard" if self._cpu.with_muldiv else "soft"

    def elaborate(self, platform):
        m = Module()

        m.submodules.minerva = self._cpu
        m.d.comb += [
            self._cpu.ibus.connect(self.ibus),
            self._cpu.dbus.connect(self.dbus),
            self._cpu.external_interrupt.eq(self.irq_external),
        ]

        return m
