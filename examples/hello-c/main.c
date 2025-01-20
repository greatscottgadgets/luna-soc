/**
 * This file is part of LUNA.
 *
 * Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdbool.h>

// Include our automatically generated resource file.
// This allows us to work with e.g. our registers no matter gt
#include "resources.h"

/**
 * Transmits a single charater over our example UART.
 */
void print_char(char c)
{
    while(!uart0_tx_ready_read());
    uart0_tx_data_write(c);
}

/**
 * Transmits a string over our UART.
 */
void uart_puts(char *str)
{
    for (char *c = str; *c; ++c) {
        print_char(*c);
    }
}

/**
 * Main firmware entry point
 */
int main(void)
{
    bool shifting_right = true;
    uint8_t led_value = 0b110000;

    // Set up our timer to periodically move the LEDs.
    timer0_reload_write(0x0C0000);
    timer0_enable_write(1);
    timer0_ev_enable_write(1);
    timer0_interrupt_enable();

    // And blink our LEDs.
    while(1) {

        // Skip all iterations that aren't our main one...
        if (timer0_counter_read()) {
            continue;
        }

        // ... compute our pattern ...
        if (shifting_right) {
            led_value >>= 1;

            if (led_value == 0b000011) {
                shifting_right = false;
                uart_puts("left!\r\n");
            }
        } else {
            led_value <<= 1;

            if (led_value == 0b110000) {
                shifting_right = true;
                uart_puts("right!\r\n");
            }
        }

        // ... and output it to the LEDs.
        leds_output_write(led_value);
    }
}
