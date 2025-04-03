
**ENDPOINT Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0000
    - [3:0]
    - write-only
    - ``number``

.. code-block:: markdown

     Endpoint register

            number: Contains the endpoint the enqueued packet is to be transmitted on. Writing to this field
                    marks the relevant packet as ready to transmit; and thus should only be written after a
                    full packet has been written into the FIFO. If no data has been placed into the DATA FIFO,
                    a zero-length packet is generated.
                    Note that any IN requests that do not match the endpoint number are automatically NAK'd.
        


**STALL Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0001
    - [0:0]
    - write-only
    - ``stalled``

.. code-block:: markdown

     Stall register

            stalled: When this field contains '1', any IN tokens targeting `epno` will be responded to with a
                     STALL token, rather than DATA or a NAK.
                     For EP0, this field will automatically be cleared when a new SETUP token is received.
        


**PID Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0002
    - [0:0]
    - write-only
    - ``toggle``

.. code-block:: markdown

     Pid register

            toggle: Sets the current PID toggle bit for the given endpoint.
        


**STATUS Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0004
    - [15:0]
    - read-only
    - ``nak``
  * - 0x0004
    - [19:16]
    - read-only
    - ``epno``
  * - 0x0004
    - [24:24]
    - read-only
    - ``idle``
  * - 0x0004
    - [25:25]
    - read-only
    - ``have``
  * - 0x0004
    - [26:26]
    - read-only
    - ``pid``

.. code-block:: markdown

     Status register

            nak:  Contains a bitmask of endpoints that have responded with a NAK since the
                  last read of this register.
            epno: Contains the endpoint being transmitted on.
            idle: This value is `1` if no packet is actively being transmitted.
            have: This value is `1` if data is present in the transmit FIFO.
            pid:  Contains the current PID toggle bit for the given endpoint.
        


**RESET Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0008
    - [0:0]
    - write-only
    - ``fifo``

.. code-block:: markdown

     Reset register

            fifo: A write to this field Clears the FIFO without transmitting.
        


**DATA Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0009
    - [7:0]
    - write-only
    - ``byte``

.. code-block:: markdown

     Data register

            Each write enqueues a byte to be transmitted; gradually building a single packet to
            be transmitted. This queue should only ever contain a single packet; it is the software's
            responsibility to handle breaking requests down into packets.
        


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
