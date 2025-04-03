
**CONTROL Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0000
    - [7:0]
    - write-only
    - ``address``

.. code-block:: markdown

     Control register

            address: Controls the current device's USB address. Should be written after a SET_ADDRESS
                     request is received. Automatically resets back to zero on a USB reset.
        


**STATUS Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0002
    - [7:0]
    - read-only
    - ``address``
  * - 0x0002
    - [11:8]
    - read-only
    - ``epno``
  * - 0x0002
    - [12:12]
    - read-only
    - ``have``

.. code-block:: markdown

     Status register

            address: Holds the current device's active USB address.
            epno:    The endpoint number associated with the most recently captured SETUP packet.
            have:    `1` iff data is available in the FIFO.
        


**RESET Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0004
    - [0:0]
    - write-only
    - ``fifo``

.. code-block:: markdown

     Reset register

            fifo: Local reset control for the SETUP handler; writing a '1' to this register clears
                  the handler state.
        


**DATA Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0005
    - [7:0]
    - read-only
    - ``byte``

.. code-block:: markdown

     Data register

            A FIFO that returns the bytes from the most recently captured SETUP packet.
            Reading a byte from this register advances the FIFO. The first eight bytes read
            from this contain the core SETUP packet.
        


**EV_ENABLE Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0010
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
  * - 0x0011
    - [0:0]
    - read-write
    - ``mask``
