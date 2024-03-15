.. list-table:: USB0_EP_OUT Register Map
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
    - A FIFO that returns the bytes from the most recently captured OUT transaction.            Reading a byte from this register advances the FIFO.
  * - 0x0004
    - [3:0]
    - read-only
    - ``data_ep``
    - Register that contains the endpoint number associated with the data in the FIFO -- that is,            the endpoint number on which the relevant data was received.
  * - 0x0008
    - [0:0]
    - write-only
    - ``reset``
    - Local reset for the OUT handler; clears the out FIFO.
  * - 0x000c
    - [3:0]
    - read-write
    - ``epno``
    - Selects the endpoint number to prime. This interface only allows priming a single endpoint at once--            that is, only one endpoint can be ready to receive data at a time. See the `enable` bit for usage.
  * - 0x0010
    - [0:0]
    - read-write
    - ``enable``
    - Controls whether any data can be received on any primed OUT endpoint. This bit is automatically cleared            on receive in order to give the controller time to read data from the FIFO. It must be re-enabled once            the FIFO has been emptied.
  * - 0x0014
    - [0:0]
    - write-only
    - ``prime``
    - Controls "priming" an out endpoint. To receive data on any endpoint, the CPU must first select            the endpoint with the `epno` register; and then write a '1' into the prime and enable register.            This prepares our FIFO to receive data; and the next OUT transaction will be captured into the FIFO.            When a transaction is complete, the `enable` bit is reset; the `prime` is not. This effectively means            that `enable` controls receiving on _any_ of the primed endpoints; while `prime` can be used to build            a collection of endpoints willing to participate in receipt.            Only one transaction / data packet is captured per `enable` write; repeated enabling is necessary            to capture multiple packets.
  * - 0x0018
    - [0:0]
    - read-write
    - ``stall``
    - Controls STALL'ing the active endpoint. Setting or clearing this bit will set or clear STALL on            the provided endpoint. Endpoint STALLs persist even after `epno` is changed; so multiple endpoints            can be stalled at once by writing their respective endpoint numbers into `epno` register and then            setting their `stall` bits.
  * - 0x001c
    - [0:0]
    - read-only
    - ``have``
    - `1` iff data is available in the FIFO.
  * - 0x0020
    - [0:0]
    - read-only
    - ``pend``
    - `1` iff an interrupt is pending
  * - 0x0024
    - [7:0]
    - read-write
    - ``address``
    - Controls the current device's USB address. Should be written after a SET_ADDRESS request is            received. Automatically resets back to zero on a USB reset.
  * - 0x0028
    - [0:0]
    - read-write
    - ``pid``
    - Contains the current PID toggle bit for the given endpoint.
  * - 0x0040
    - [0:0]
    - read-only
    - ``status``
    - usb0_ep_out status register field
  * - 0x0044
    - [0:0]
    - read-write
    - ``pending``
    - usb0_ep_out pending register field
  * - 0x0048
    - [0:0]
    - read-write
    - ``enable``
    - usb0_ep_out enable register field
