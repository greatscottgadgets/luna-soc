#![no_std]
#![no_main]

use log::info;
use panic_halt as _;
use riscv_rt::entry;
use lunasoc_hal::hal::delay::DelayNs;

use firmware::{pac, hal};
use hal::Serial0;
use hal::Timer0;

#[riscv_rt::pre_init]
unsafe fn pre_main() {
    pac::cpu::vexriscv::flush_icache();
    pac::cpu::vexriscv::flush_dcache();
}

#[entry]
fn main() -> ! {
    let peripherals = pac::Peripherals::take().unwrap();
    let leds = &peripherals.LEDS;

    // initialize logging
    let serial = Serial0::new(peripherals.UART0);
    firmware::log::init(serial);

    let mut timer = Timer0::new(peripherals.TIMER0, pac::clock::sysclk());
    let mut counter = 0;
    let mut direction = true;
    let mut led_state = 0b110000;

    info!("Peripherals initialized, entering main loop.");

    loop {
        timer.delay_ms(100);

        if direction {
            led_state >>= 1;
            if led_state == 0b000011 {
                direction = false;
                info!("left: {}", counter);
            }
        } else {
            led_state <<= 1;
            if led_state == 0b110000 {
                direction = true;
                info!("right: {}", counter);
            }
        }

        leds.output().write(|w| unsafe { w.bits(led_state) });
        counter += 1;
    }
}
