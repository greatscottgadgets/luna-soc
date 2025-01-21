#
# This file is part of LUNA.
#
# Copyright (c) 2020-2025 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

import logging
import os
import sys

from luna                            import configure_default_logging
from luna.gateware.usb.usb2.device   import USBDevice

from amaranth                        import *
from amaranth.lib                    import wiring

from amaranth_soc                    import csr, gpio, wishbone
from amaranth_soc.csr.wishbone       import WishboneCSRBridge

from luna_soc.gateware.cpu           import InterruptController, VexRiscv
from luna_soc.gateware.core          import blockram, timer, uart
from luna_soc.gateware.provider      import cynthion as provider

from luna_soc.util.readbin           import get_mem_data


CLOCK_FREQUENCIES_MHZ = {
    'sync': 60
}

# - HelloSoc ------------------------------------------------------------------

class HelloSoc(wiring.Component):
    def __init__(self, clock_frequency_hz, domain):
        super().__init__({})

        self.clock_frequency_hz = clock_frequency_hz
        self.domain = domain

        # configuration
        blockram_base = 0x00000000
        blockram_size = 32768

        csr_base             = 0xf0000000
        leds_base            = 0x00000000
        uart0_base           = 0x00000300
        timer0_base          = 0x00000500

        # cpu
        self.cpu = VexRiscv(
            reset_addr=blockram_base,
            variant="cynthion"
        )

        # interrupt controller
        self.interrupt_controller = InterruptController(width=len(self.cpu.irq_external))

        # bus
        self.wb_arbiter  = wishbone.Arbiter(
            addr_width=30,
            data_width=32,
            granularity=8,
            features={"cti", "bte", "err"}
        )
        self.wb_decoder  = wishbone.Decoder(
            addr_width=30,
            data_width=32,
            granularity=8,
            features={"cti", "bte", "err"}
        )

        # ... read our firmware binary ...
        filename = "build/firmware.bin"
        firmware = get_mem_data(filename, data_width=32, endianness="little")
        if not firmware:
            logging.warning(f"Firmware file '{filename}' could not be located.")
            firmware = []

        # blockram
        # TODO given that we now have it at our disposal, consider using:
        #   https://github.com/amaranth-lang/amaranth-soc/blob/main/amaranth_soc/wishbone/sram.py
        self.blockram = blockram.Peripheral(size=blockram_size, init=firmware)
        self.wb_decoder.add(self.blockram.bus, addr=blockram_base, name="blockram")

        # csr decoder
        self.csr_decoder = csr.Decoder(addr_width=28, data_width=8)

        # leds
        self.led_count = 6
        self.leds = gpio.Peripheral(pin_count=self.led_count, addr_width=3, data_width=8)
        self.csr_decoder.add(self.leds.bus, addr=leds_base, name="leds")

        # uart0
        uart_baud_rate = 115200
        divisor = int(clock_frequency_hz // uart_baud_rate)
        self.uart0 = uart.Peripheral(divisor=divisor)
        self.csr_decoder.add(self.uart0.bus, addr=uart0_base, name="uart0")

        # timer0
        self.timer0 = timer.Peripheral(width=32)
        self.csr_decoder.add(self.timer0.bus, addr=timer0_base, name="timer0")
        self.interrupt_controller.add(self.timer0, number=0, name="timer0")

        # wishbone csr bridge
        self.wb_to_csr = WishboneCSRBridge(self.csr_decoder.bus, data_width=32)
        self.wb_decoder.add(self.wb_to_csr.wb_bus, addr=csr_base, sparse=False, name="wb_to_csr")


    def elaborate(self, platform):
        m = Module()

        # bus
        m.submodules += [self.wb_arbiter, self.wb_decoder]
        wiring.connect(m, self.wb_arbiter.bus, self.wb_decoder.bus)

        # cpu
        m.submodules += self.cpu
        self.wb_arbiter.add(self.cpu.ibus)
        self.wb_arbiter.add(self.cpu.dbus)

        # interrupt controller
        m.submodules += self.interrupt_controller
        # TODO wiring.connect(m, self.cpu.irq_external, self.interrupt_controller)
        m.d.comb += self.cpu.irq_external.eq(self.interrupt_controller.pending)

        # blockram
        m.submodules += self.blockram

        # csr decoder
        m.submodules += self.csr_decoder

        # leds
        led_provider = provider.LEDProvider("led", pin_count=self.led_count)
        m.submodules += [led_provider, self.leds]
        for n in range(self.led_count):
            wiring.connect(m, self.leds.pins[n], led_provider.pins[n])

        # uart0
        uart0_provider = provider.UARTProvider("uart", 0)
        m.submodules += [uart0_provider, self.uart0]
        wiring.connect(m, self.uart0.pins, uart0_provider.pins)

        # timer0
        m.submodules += self.timer0

        # wishbone csr bridge
        m.submodules += self.wb_to_csr

        # wire up the cpu external reset signal
        try:
            user1_io = platform.request("button_user")
            m.d.comb += self.cpu.ext_reset.eq(user1_io.i)
        except:
            logging.warning("Platform does not support a user button for cpu reset")

        return DomainRenamer({
            "sync": self.domain,
        })(m)


# - module: Top ---------------------------------------------------------------

class Top(Elaboratable):
    def __init__(self, clock_frequency_hz, domain="sync"):
        self.clock_frequency_hz = clock_frequency_hz
        self.domain = domain

        self.soc = HelloSoc(clock_frequency_hz=self.clock_frequency_hz, domain=self.domain)

    def elaborate(self, platform):
        m = Module()

        # generate our domain clocks/resets
        m.submodules.car = platform.clock_domain_generator(clock_frequencies=CLOCK_FREQUENCIES_MHZ)

        # add soc to design
        m.submodules += self.soc

        return m


# - main ----------------------------------------------------------------------

if __name__ == "__main__":
    from luna                    import configure_default_logging
    from luna.gateware.platform  import get_appropriate_platform
    from luna_soc                import top_level_cli

    # configure logging
    configure_default_logging()
    logging.getLogger().setLevel(logging.DEBUG)

    # select platform
    platform = get_appropriate_platform()
    if platform is None:
        logging.error("Failed to identify a supported platform")
        sys.exit(1)

    # configure domain
    domain = "sync"

    # configure clock frequency
    clock_frequency_hz = int(CLOCK_FREQUENCIES_MHZ[domain] * 1e6)
    logging.info(f"Building for {platform} with domain {domain} and clock frequency: {clock_frequency_hz}")

    # create design
    design = Top(clock_frequency_hz=int(60e6), domain=domain)

    # invoke cli
    _overrides = {
        "debug_verilog": False,
        "verbose": False,
    }
    top_level_cli(design, **_overrides)
