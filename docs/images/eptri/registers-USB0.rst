.. list-table:: USB0 Register Map
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Name
    - Description
  * - 0x0000
    - [0:0]
    - read-write
    - ``connect``
    - Set this bit to '1' to allow the associated USB device to connect to a host.
  * - 0x0004
    - [1:0]
    - read-only
    - ``speed``
    - Indicates the current speed of the USB device. 0 indicates High; 1 => Full,            2 => Low, and 3 => SuperSpeed (incl SuperSpeed+).
  * - 0x0008
    - [0:0]
    - read-write
    - ``low_speed_only``
    - Set this bit to '1' to force the device to operate at low speed.
  * - 0x000c
    - [0:0]
    - read-write
    - ``full_speed_only``
    - Set this bit to '1' to force the device to operate at full speed.
  * - 0x0010
    - [0:0]
    - read-only
    - ``status``
    - usb0 status register field
  * - 0x0014
    - [0:0]
    - read-write
    - ``pending``
    - usb0 pending register field
  * - 0x0018
    - [0:0]
    - read-write
    - ``enable``
    - usb0 enable register field
