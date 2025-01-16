from amaranth              import *
from amaranth.lib          import wiring
from amaranth.lib.wiring   import In, Out

# type aliases only in py 3.12 :-(
# type InterruptMap = dict[int, (str, wiring.Component)]
InterruptMap = dict[int, (str, wiring.Component)]


class InterruptController(wiring.Component):
    def __init__(self, *, width):
        super().__init__({
            "pending":  Out(unsigned(width)),
        })

        self._interrupts: InterruptMap = dict()

    def interrupts(self) -> InterruptMap:
        return self._interrupts

    # TODO add line or peripheral ?
    # if we go by convention it would only be the line
    def add(self, peripheral, *, name, number=None):
        if number is None:
            raise ValueError("TODO")
        if number in self._interrupts.keys():
            raise ValueError(f"IRQ number '{number}' has already been used.")
        if peripheral in self._interrupts.values(): # TODO fix this -- values is a tuple now
            raise ValueError(f"Peripheral '{peripheral}' has already been added.")
        self._interrupts[number] = (name, peripheral)

    def elaborate(self, platform):
        m = Module()

        for number, (name, peripheral) in self._interrupts.items():
            m.d.comb += self.pending[number].eq(peripheral.irq)

        return m
