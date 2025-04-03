
**CONTROL Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0000
    - [0:0]
    - read-write
    - ``connect``
  * - 0x0000
    - [8:8]
    - read-write
    - ``low_speed_only``
  * - 0x0000
    - [9:9]
    - read-write
    - ``full_speed_only``

.. code-block:: markdown

    Control register

            connect:         Set this bit to '1' to allow the associated USB device to connect to a host.
            low_speed_only:  Set this bit to '1' to force the device to operate at low speed.
            full_speed_only: Set this bit to '1' to force the device to operate at full speed.
        


**STATUS Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0002
    - [1:0]
    - read-only
    - ``speed``

.. code-block:: markdown

    Status register

            speed: Indicates the current speed of the USB device. 0 indicates High; 1 => Full,
                   2 => Low, and 3 => SuperSpeed (incl SuperSpeed+).
        


**EV_ENABLE Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0008
    - [0:0]
    - read-write
    - ``mask``

**EV_PENDING Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0009
    - [0:0]
    - read-write
    - ``mask``
