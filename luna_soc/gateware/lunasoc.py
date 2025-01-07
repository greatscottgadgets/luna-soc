from amaranth                import Elaboratable, Module

from amaranth_soc            import wishbone
from amaranth_soc.memory     import MemoryMap
from amaranth_soc.periph     import ConstantMap

from amaranth_stdio.serial   import AsyncSerial

#from lambdasoc.periph.intc   import GenericInterruptController
#from lambdasoc.periph.serial import AsyncSerialPeripheral
#from lambdasoc.periph.timer  import TimerPeripheral

from .csr.base         import Peripheral
from .wishbone         import SRAMPeripheral, WishboneRAM, WishboneROM


# - LunaSoC -------------------------------------------------------------------

class LunaSoC(Elaboratable):
    """ Class used for building simple system-on-a-chip architectures.

    Intended to facilitate custom SoC designs by providing a wrapper
    that can be updated as amaranth-soc matures.

    LUNA-SOC devices integrate:
        - A RiscV processor.
        - One or more read-only or read-write memories.
        - A number of amaranth-soc peripherals.

    The current implementation uses a single, 32-bit wide Wishbone bus
    as the system's backend; and uses amaranth-soc as its backing
    technology.
    """

    def __init__(self, cpu, clock_frequency=int(60e6), with_debug=False):

        self.cpu             = cpu
        self.clock_frequency = clock_frequency

        # create system bus
        self._bus_arbiter = wishbone.Arbiter(addr_width=30, data_width=32, granularity=8,
                                             features={"cti", "bte", "err"})
        self._bus_decoder = wishbone.Decoder(addr_width=30, data_width=32, granularity=8,
                                             alignment=0,
                                             features={"cti", "bte", "err"})
        self._bus_arbiter.add(cpu.ibus)
        self._bus_arbiter.add(cpu.dbus)

        # create interrupt controller
        try:
            self.cpu_irq_external = cpu.irq_external
        except:
            raise ValueError(f"Unsupported CPU: {cpu}")
        self.intc = GenericInterruptController(width=len(self.cpu_irq_external))

        # random state it would be nice to get rid of
        self._interrupt_index = 0
        self._interrupt_map = {}
        self._peripherals = []

    def add_core_peripherals(self, uart_pins, uart_baud_rate=115200, internal_sram_addr=0x40000000, internal_sram_size=int(32768), internal_sram_init=None):

        self.internal_sram_addr = internal_sram_addr
        self.internal_sram_size = internal_sram_size

        # bootrom configuration
        bootrom_addr       = 0x00000000
        bootrom_size       = 0x0020 #  32B - just enough to stop the bus from freaking out

        # timer0 configuration
        timer_addr  = 0xf0000100
        timer_width = 32

        # uart0 configuration
        uart_addr  = 0xf0000200
        uart_core = AsyncSerial(
            data_bits = 8,
            divisor   = int(self.clock_frequency // uart_baud_rate),
            pins      = uart_pins,
        )

        # add a smol empty bootrom to keep vexriscv happy at reset
        self.bootrom = SRAMPeripheral(size=bootrom_size, writable=False)
        self.add_peripheral(self.bootrom, addr=bootrom_addr)

        # add mainram
        self.mainram = SRAMPeripheral(size=internal_sram_size, init=internal_sram_init)
        self.add_peripheral(self.mainram, addr=internal_sram_addr)

        # add timer0
        self.timer = TimerPeripheral(width=timer_width)
        self.add_peripheral(self.timer, addr=timer_addr)

        # add uart0
        self.uart = AsyncSerialPeripheral(core=uart_core)
        self.add_peripheral(self.uart, addr=uart_addr)


    def add_peripheral(self, peripheral: Peripheral, *, as_submodule=True, **kwargs) -> Peripheral:
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


    def elaborate(self, platform):
        m = Module()

        # add cpu, bus and interrupt controller
        m.submodules.cpu        = self.cpu
        m.submodules.arbiter    = self._bus_arbiter
        m.submodules.decoder    = self._bus_decoder
        m.submodules.intc       = self.intc

        # add peripherals
        for peripheral in self._peripherals:
            m.submodules += peripheral

        # connect interrupt lines
        m.d.comb += [
            self._bus_arbiter.bus.connect(self._bus_decoder.bus),
            self.cpu_irq_external.eq(self.intc.ip),
        ]

        return m


    # - properties ------------------------------------------------------------

    @property
    def memory_map(self):
        return self._bus_decoder.bus.memory_map


    # - integration API -- TODO remove these entirely and call Introspect directly from generate/gen*

    def resources(self):
        from ..generate        import Introspect
        return Introspect(self).resources()

    def range_for_peripheral(self, target_peripheral: Peripheral):
        from ..generate        import Introspect
        return Introspect(self).range_for_peripheral(target_peripheral)

    def irq_for_peripheral_window(self, target_peripheral_window: MemoryMap):
        from ..generate        import Introspect
        return Introspect(self).irq_for_peripheral_window(target_peripheral_window)
