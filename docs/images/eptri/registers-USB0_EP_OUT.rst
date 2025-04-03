
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
    - read-write
    - ``address``

.. code-block:: markdown

     Control register

            address: Controls the current device's USB address. Should be written after a SET_ADDRESS request
                     is received. Automatically resets back to zero on a USB reset.
        


**ENDPOINT Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0001
    - [3:0]
    - read-write
    - ``number``

.. code-block:: markdown

     Endpoint register

            number: Selects the endpoint number to prime. This interface allows priming multiple endpoints
            at once. That is, multiple endpoints can be ready to receive data at a time. See the `prime`
            and `enable` bits for usage.
        


**ENABLE Register**

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
    - ``enabled``

.. code-block:: markdown

     Enable register

            enabled: Controls whether any data can be received on any primed OUT endpoint. This bit is
                     automatically cleared on receive in order to give the controller time to read data
                     from the FIFO. It must be re-enabled once the FIFO has been emptied.
        


**PRIME Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0003
    - [0:0]
    - write-only
    - ``primed``

.. code-block:: markdown

     Prime register

            primed: Controls "priming" an out endpoint. To receive data on any endpoint, the CPU must first
                    select the endpoint with the `epno` register; and then write a '1' into the prime and
                    enable register. This prepares our FIFO to receive data; and the next OUT transaction will
                    be captured into the FIFO.

                    When a transaction is complete, the `enable` bit is reset; the `prime` is not. This
                    effectively means that `enable` controls receiving on _any_ of the primed endpoints;
                    while `prime` can be used to build a collection of endpoints willing to participate in
                    receipt.

                    Note that this does not apply to the control endpoint. Once the control endpoint has
                    received a packet it will be un-primed and need to be re-primed before it can receive
                    again. This is to ensure that we can establish an order on the receipt of the setup
                    packet and any associated data.

                    Only one transaction / data packet is captured per `enable` write; repeated enabling is
                    necessary to capture multiple packets.
        


**STALL Register**

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
    - ``stalled``

.. code-block:: markdown

     Stall register

            stalled: Controls STALL'ing the active endpoint. Setting or clearing this bit will set or clear
                     STALL on the provided endpoint. Endpoint STALLs persist even after `epno` is changed; so
                     multiple endpoints can be stalled at once by writing their respective endpoint numbers
                     into `epno` register and then setting their `stall` bits.
        


**PID Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0005
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
  * - 0x0006
    - [3:0]
    - read-only
    - ``epno``
  * - 0x0006
    - [8:8]
    - read-only
    - ``have``
  * - 0x0006
    - [9:9]
    - read-only
    - ``pid``

.. code-block:: markdown

     Status register

            epno: Contains the endpoint number associated with the data in the FIFO -- that is,
                  the endpoint number on which the relevant data was received.
            have: `1` iff data is available in the FIFO.
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

            fifo: Local reset for the OUT handler; clears the out FIFO.
        


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
    - read-only
    - ``byte``

.. code-block:: markdown

     Data register

            Read-only register. A FIFO that returns the bytes from the most recently captured OUT transaction.
            Reading a byte from this register advances the FIFO.

            byte:    Contains the most recently received byte.
        


**EV_ENABLE Register**

.. list-table::
  :widths: 100 100 100 500
  :header-rows: 1

  * - Offset
    - Range
    - Access
    - Field
  * - 0x0020
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
  * - 0x0021
    - [0:0]
    - read-write
    - ``mask``
