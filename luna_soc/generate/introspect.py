#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

"""Introspection tools for SoC designs."""

import amaranth_soc

import lambdasoc
from lambdasoc.soc.cpu import CPUSoC, BIOSBuilder

import logging


class Introspect:
    def __init__(self, soc: CPUSoC):
        self._soc = soc

    # - public API --

    # TODO s/resources/peripherals
    # TODO attach irq to peripheral if there is one so we don't have to maintain it separately
    # TODO add a "memories()" ?
    def resources(self, omit_bios_mem=True):
        """ Creates an iterator over each of the device's addressable resources.

        Yields (MemoryMap, ResourceInfo, address, size) for each resource.

        Parameters:
            omit_bios_mem -- If True, BIOS-related memories are skipped when generating our
                             resource listings. This hides BIOS resources from the application.
        """

        # Grab the memory map for this SoC...
        memory_map = self._soc._bus_decoder.bus.memory_map

        # ... find each addressable peripheral...
        window: amaranth_soc.memory.MemoryMap
        for window, (window_start, _end, _granularity) in memory_map.windows():

            # Grab the resources for this peripheral
            resources = window.all_resources()

            # ... find the peripheral's resources...
            resource_info: amaranth_soc.memory.ResourceInfo
            for resource_info in resources:
                resource = resource_info.resource
                register_offset = resource_info.start
                register_end_offset = resource_info.end
                _local_granularity = resource_info.width

                # TODO
                if False: #self._soc._build_bios and omit_bios_mem:
                    # If we're omitting bios resources, skip the BIOS ram/rom.
                    if (self._soc.mainram._mem is resource) or (self._soc.bootrom._mem is resource):
                        continue

                # ... and extract the peripheral's range/vitals...
                size = register_end_offset - register_offset
                yield window, resource_info, window_start + register_offset, size


    def range_for_peripheral(self, target_peripheral: lambdasoc.periph.Peripheral):
        """ Returns size information for the given peripheral.
        Returns:
            addr, size -- if the given size is known; or
            None, None    if not
        """

        # Grab the memory map for this SoC...
        memory_map = self._soc._bus_decoder.bus.memory_map

        # Search our memory map for the target peripheral.
        resource_info: amaranth_soc.memory.ResourceInfo
        for resource_info in memory_map.all_resources():
            if resource_info.name[0] is target_peripheral.name:
                return resource_info.start, (resource_info.end - resource_info.start)

        return None, None


    def irq_for_peripheral_window(self, target_peripheral_window: amaranth_soc.memory.MemoryMap):
        """ Returns any interrupt associated with the given peripheral.
        Returns:
            irqno, peripheral -- if the given peripheral has an interrupt; or
            None, None    if not
        """
        for irqno, peripheral in self._soc._interrupt_map.items():
            if peripheral.name is target_peripheral_window.name:
                return irqno, peripheral

        return None, None


    def log_resources(self):
        """ Logs a summary of our resource utilization to our running logs. """

        # Grab the memory map for this SoC...
        memory_map = self._soc._bus_decoder.bus.memory_map

        # Resource addresses:
        logging.info("Physical address allocations:")
        resource_info: amaranth_soc.memory.ResourceInfo
        for resource_info in memory_map.all_resources():
            start = resource_info.start
            end = resource_info.end
            name = "_".join(resource_info.name)
            peripheral = resource_info.resource
            logging.info(f"    {start:08x}-{end:08x}: {name} {peripheral}")

        logging.info("")

        # IRQ numbers
        logging.info("IRQ allocations:")
        for irq, peripheral in self._soc._interrupt_map.items():
            logging.info(f"    {irq}: {peripheral.name}")

        logging.info("")

        # Main memory.
        if self._soc.mainram:
            memory_location = self.main_ram_address()
            logging.info(f"Main memory at 0x{memory_location:08x}; upload using:")
            logging.info(f"    flterm --kernel <your_firmware> --kernel-addr 0x{memory_location:08x} --speed 115200")
            logging.info("or")
            logging.info(f"    lxterm --kernel <your_firmware> --kernel-adr 0x{memory_location:08x} --speed 115200")

        logging.info("")

    def main_ram_address(self):
        """ Returns the address of the main system RAM. """
        start, _  = self.range_for_peripheral(self._soc.mainram)
        return start
