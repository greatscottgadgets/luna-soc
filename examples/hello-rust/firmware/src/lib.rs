#![no_std]
#![no_main]

pub use lunasoc_pac as pac;

pub mod log;
pub mod hal {
    use crate::pac;

    lunasoc_hal::impl_serial! {
        Serial0: pac::UART0,
    }

    lunasoc_hal::impl_timer! {
        Timer0: pac::TIMER0,
    }
}
