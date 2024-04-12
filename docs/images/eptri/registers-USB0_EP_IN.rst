.. list-table:: USB0_EP_IN Register Map
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Name
    - Description
  * - 0x0000
    - [7:0]
    - write-only
    - ``data``
    - Write-only register. Each write enqueues a byte to be transmitted; gradually building            a single packet to be transmitted. This queue should only ever contain a single packet;            it is the software's responsibility to handle breaking requests down into packets.
  * - 0x0004
    - [3:0]
    - read-write
    - ``epno``
    - Contains the endpoint the enqueued packet is to be transmitted on. Writing this register            marks the relevant packet as ready to transmit; and thus should only be written after a            full packet has been written into the FIFO. If no data has been placed into the DATA FIFO,            a zero-length packet is generated.            Note that any IN requests that do not match the endpoint number are automatically NAK'd.
  * - 0x0008
    - [0:0]
    - write-only
    - ``reset``
    - A write to this register clears the FIFO without transmitting.
  * - 0x000c
    - [0:0]
    - read-write
    - ``stall``
    - When this register contains '1', any IN tokens targeting `epno` will be responded to with a            STALL token, rather than DATA or a NAK.            For EP0, this register will automatically be cleared when a new SETUP token is received.
  * - 0x0010
    - [0:0]
    - read-only
    - ``idle``
    - This value is `1` if no packet is actively being transmitted.
  * - 0x0014
    - [0:0]
    - read-only
    - ``have``
    - This value is `1` if data is present in the transmit FIFO.
  * - 0x0018
    - [0:0]
    - read-only
    - ``pend``
    - `1` iff an interrupt is pending
  * - 0x001c
    - [0:0]
    - read-write
    - ``pid``
    - Contains the current PID toggle bit for the given endpoint.
  * - 0x0020
    - [15:0]
    - read-only
    - ``nak``
    - Read-only register. Contains a bitmask of endpoints that have responded with a NAK since the            last read of this register.
  * - 0x0040
    - [0:0]
    - read-only
    - ``status``
    - usb0_ep_in status register field
  * - 0x0044
    - [0:0]
    - read-write
    - ``pending``
    - usb0_ep_in pending register field
  * - 0x0048
    - [0:0]
    - read-write
    - ``enable``
    - usb0_ep_in enable register field
