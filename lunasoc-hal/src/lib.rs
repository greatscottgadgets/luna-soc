#![cfg_attr(not(test), no_std)]
#![allow(clippy::inline_always)]
#![allow(clippy::must_use_candidate)]

#[cfg(test)]
#[macro_use]
extern crate std;

// modules
pub mod serial;
pub mod timer;

pub use embedded_hal as hal;
pub use embedded_hal_nb as hal_nb;

#[macro_use]
extern crate bitflags;

pub use nb;
