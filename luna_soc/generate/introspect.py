#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

"""Introspection tools for SoC designs."""

import logging

from collections          import defaultdict

from amaranth.lib         import wiring

from amaranth_soc         import csr
from amaranth_soc.memory  import MemoryMap, ResourceInfo


def introspect(design: wiring.Component):
    memory_map: MemoryMap = design.wb_decoder.bus.memory_map

    csr_base        = _csr_base(memory_map)
    csr_peripherals = _csr_peripherals(memory_map)
    wb_peripherals  = _wb_peripherals(memory_map)
    interrupts      = _interrupts(design)

    print(f"csr_base: 0x{csr_base:08x}")




def _interrupts(design: wiring.Component):
    return design.interrupt_controller.interrupts


def _csr_base(memory_map: MemoryMap) -> int:
    """Scan a memory map for the starting address for csr peripheral registers."""
    window: MemoryMap
    name:   MemoryMap.Name
    for window, name, (start, end, ratio) in memory_map.windows():
        if name[0] == "wb_to_csr":
            return start

def _csr_peripherals(memory_map: MemoryMap) -> dict[MemoryMap.Name, list[ResourceInfo]]:
    """Scan a memory map for csr peripheral registers."""

    # group registers by peripheral
    csr_peripherals = defaultdict(list)

    # scan memory map for peripheral registers
    window: MemoryMap
    name:   MemoryMap.Name
    for window, name, (start, end, ratio) in memory_map.windows():
        resource_info: ResourceInfo
        for resource_info in window.all_resources():
            peripheral: MemoryMap.Name = resource_info.path[0]
            register:   csr.Register   = resource_info.resource
            if issubclass(register.__class__, csr.Register):
                csr_peripherals[peripheral].append(resource_info)

    return csr_peripherals

def _wb_peripherals(memory_map: MemoryMap) -> dict[
        MemoryMap.Name,
        list[
            tuple[
                wiring.Component,
                MemoryMap.Name,
                (int, int)
            ]
        ]]:
    """Scan a memory map for wishbone peripherals."""

    # group by peripheral
    wb_peripherals = defaultdict(list)

    # scan memory map for wb peripherals
    window: MemoryMap
    for window, name, (start, end, ratio) in memory_map.windows():
        # window.resources() yields a tuple: `resource, resource_name, (start, end)`
        # where resource is the actual peripheral e.g. `core.blockram.Peripheral`
        for resource, path, (start, stop) in window.resources():
            wb_peripherals[name].append((resource, path, (start, stop)))

    return wb_peripherals





# class Introspect:
#     def __init__(self, soc: LunaSoC):
#         self._soc = soc

#     # - public API --

#     # TODO s/resources/peripherals
#     # TODO attach irq to peripheral if there is one so we don't have to maintain it separately
#     # TODO add a "memories()" ?
#     def resources(self):
#         """ Creates an iterator over each of the device's addressable resources.

#         Yields (MemoryMap, ResourceInfo, address, size) for each resource.
#         """

#         # Grab the memory map for this SoC...
#         memory_map = self._soc._bus_decoder.bus.memory_map

#         # ... find each addressable peripheral...
#         window: amaranth_soc.memory.MemoryMap
#         for window, (window_start, _end, _granularity) in memory_map.windows():

#             # Grab the resources for this peripheral
#             resources = window.all_resources()

#             # ... find the peripheral's resources...
#             resource_info: amaranth_soc.memory.ResourceInfo
#             for resource_info in resources:
#                 resource = resource_info.resource
#                 register_offset = resource_info.start
#                 register_end_offset = resource_info.end
#                 _local_granularity = resource_info.width

#                 # ... and extract the peripheral's range/vitals...
#                 size = register_end_offset - register_offset
#                 yield window, resource_info, window_start + register_offset, size


#     def range_for_peripheral(self, target_peripheral: Peripheral):
#         """ Returns size information for the given peripheral.

#         Returns:
#             addr, size : if the given size is known; or None, None if not
#         """

#         # Grab the memory map for this SoC...
#         memory_map = self._soc._bus_decoder.bus.memory_map

#         # Search our memory map for the target peripheral.
#         resource_info: amaranth_soc.memory.ResourceInfo
#         for resource_info in memory_map.all_resources():
#             if resource_info.name[0] is target_peripheral.name:
#                 return resource_info.start, (resource_info.end - resource_info.start)

#         return None, None


#     def irq_for_peripheral_window(self, target_peripheral_window: amaranth_soc.memory.MemoryMap):
#         """ Returns any interrupt associated with the given peripheral.

#         Returns:
#             irqno, peripheral : if the given peripheral has an interrupt; or None, None if not
#         """
#         for irqno, peripheral in self._soc._interrupt_map.items():
#             if peripheral.name is target_peripheral_window.name:
#                 return irqno, peripheral

#         return None, None


#     def log_resources(self):
#         """ Logs a summary of our resource utilization to our running logs. """

#         # Grab the memory map for this SoC...
#         memory_map = self._soc._bus_decoder.bus.memory_map

#         # Resource addresses:
#         logging.info("Physical address allocations:")
#         resource_info: amaranth_soc.memory.ResourceInfo
#         for resource_info in memory_map.all_resources():
#             start = resource_info.start
#             end = resource_info.end
#             name = "_".join(resource_info.name)
#             peripheral = resource_info.resource
#             logging.info(f"    {start:08x}-{end:08x}: {name} {peripheral}")

#         logging.info("")

#         # IRQ numbers
#         logging.info("IRQ allocations:")
#         for irq, peripheral in self._soc._interrupt_map.items():
#             logging.info(f"    {irq}: {peripheral.name}")

#         logging.info("")

#         # Main memory.
#         if hasattr(self._soc, "mainram"):
#             memory_location = self.main_ram_address()
#             logging.info(f"Main memory at: 0x{memory_location:08x}")

#         logging.info("")

#     def main_ram_address(self):
#         """ Returns the address of the main system RAM. """
#         if hasattr(self._soc, "mainram"):
#             start, _  = self.range_for_peripheral(self._soc.mainram)
#         else:
#             start, _  = self.range_for_peripheral(self._soc.scratchpad)
#         return start
