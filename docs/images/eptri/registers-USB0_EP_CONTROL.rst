.. list-table:: USB0_EP_CONTROL Register Map
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Name
    - Description
  * - 0x0000
    - [7:0]
    - read-only
    - ``data``
    - A FIFO that returns the bytes from the most recently captured SETUP packet.            Reading a byte from this register advances the FIFO. The first eight bytes read            from this contain the core SETUP packet.
  * - 0x0004
    - [0:0]
    - write-only
    - ``reset``
    - Local reset control for the SETUP handler; writing a '1' to this register clears the handler state.
  * - 0x0008
    - [3:0]
    - read-only
    - ``epno``
    - The endpoint number associated with the most recently captured SETUP packet.
  * - 0x000c
    - [0:0]
    - read-only
    - ``have``
    - `1` iff data is available in the FIFO.
  * - 0x0010
    - [0:0]
    - read-only
    - ``pend``
    - `1` iff an interrupt is pending
  * - 0x0014
    - [7:0]
    - read-write
    - ``address``
    - Controls the current device's USB address. Should be written after a SET_ADDRESS request is            received. Automatically resets back to zero on a USB reset.
  * - 0x0020
    - [0:0]
    - read-only
    - ``status``
    - usb0_ep_control status register field
  * - 0x0024
    - [0:0]
    - read-write
    - ``pending``
    - usb0_ep_control pending register field
  * - 0x0028
    - [0:0]
    - read-write
    - ``enable``
    - usb0_ep_control enable register field
