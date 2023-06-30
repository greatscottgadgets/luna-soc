#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

"""Generate a SVD file for SoC designs."""

import amaranth

import amaranth_soc
from  amaranth_soc.memory import MemoryMap, ResourceInfo

from lambdasoc.soc.cpu import CPUSoC

from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment, tostring

from os import path
import logging

class GenSVD:

    def __init__(self, soc: CPUSoC):
        self._soc = soc


    # - svd generation --------------------------------------------------------

    def generate_svd(self, file=None, vendor="amaranth-soc", name="soc", description=None):
        """ Generate a svd file for the given SoC"""
        device = _generate_section_device(self._soc, vendor, name, description)

        # <peripherals />
        peripherals = SubElement(device, "peripherals")

        window: MemoryMap
        for window, (start, stop, ratio) in self._soc.memory_map.windows():
            if window.name in ["bootrom", "scratchpad", "mainram", "ram", "rom"]:
                logging.info("Skipping non-peripheral resource: {}".format(window.name))
                continue

            peripheral = _generate_section_peripheral(peripherals, self._soc, window, start, stop, ratio)
            registers = SubElement(peripheral, "registers")

            resource_info: ResourceInfo
            for resource_info in window.all_resources():
                register = _generate_section_register(registers, window, resource_info)
                fields = SubElement(register, "fields")
                field = _generate_section_field(fields, window, resource_info)

        # <vendorExtensions />
        vendorExtensions = SubElement(device, "vendorExtensions")

        memoryRegions = SubElement(vendorExtensions, "memoryRegions")

        window: MemoryMap
        for window, (start, stop, ratio) in self._soc.memory_map.windows():
            if window.name not in ["bootrom", "scratchpad", "mainram", "ram", "rom"]:
                continue

            memoryRegion = SubElement(memoryRegions, "memoryRegion")
            el = SubElement(memoryRegion, "name")
            el.text = window.name.upper()
            el = SubElement(memoryRegion, "baseAddress")
            el.text = "0x{:08x}".format(start)
            el = SubElement(memoryRegion, "size")
            el.text = "0x{:08x}".format(stop - start)

        constants = SubElement(vendorExtensions, "constants")  # TODO

        # dump
        output = ElementTree.tostring(device, 'utf-8')
        output = minidom.parseString(output)
        #output = output.toprettyxml(indent="  ")
        output = output.toprettyxml(indent="  ", encoding="utf-8")

        # write to file
        file.write(str(output.decode("utf-8")))
        file.close()


# - section helpers -----------------------------------------------------------

def _generate_section_device(soc: CPUSoC, vendor, name, description):
    device = Element("device")
    device.set("schemaVersion", "1.1")
    device.set("xmlns:xs", "http://www.w3.org/2001/XMLSchema-instance")
    device.set("xs:noNamespaceSchemaLocation", "CMSIS-SVD.xsd")
    el = SubElement(device, "vendor")
    el.text = vendor
    el = SubElement(device, "name")
    el.text = name.upper()
    el = SubElement(device, "description")
    if description is None:
        el.text = "TODO device.description"
    else:
        el.text = description
    el = SubElement(device, "addressUnitBits")
    el.text = "8"          # TODO
    el = SubElement(device, "width")
    el.text = "32"         # TODO
    el = SubElement(device, "size")
    el.text = "32"         # TODO
    el = SubElement(device, "access")
    el.text = "read-write"
    el = SubElement(device, "resetValue")
    el.text = "0x00000000" # TODO
    el = SubElement(device, "resetMask")
    el.text = "0xFFFFFFFF" # TODO

    return device


def _generate_section_peripheral(peripherals: Element, soc, window: MemoryMap, start, stop, ratio):
    peripheral = SubElement(peripherals, "peripheral")
    el = SubElement(peripheral, "name")
    el.text = window.name.upper()
    el = SubElement(peripheral, "groupName")
    el.text = window.name.upper()
    el = SubElement(peripheral, "baseAddress")
    el.text = "0x{:08x}".format(start)

    addressBlock = SubElement(peripheral, "addressBlock")
    el = SubElement(addressBlock, "offset")
    el.text = "0" # TODO
    el = SubElement(addressBlock, "size")     # TODO
    el.text = "0x{:02x}".format(stop - start) # TODO
    el = SubElement(addressBlock, "usage")
    el.text = "registers" # TODO

    target_irqno, target_peripheral = soc.irq_for_peripheral_window(window)
    if target_peripheral is not None:
        interrupt = SubElement(peripheral, "interrupt")
        el = SubElement(interrupt, "name")
        el.text = target_peripheral.name
        el = SubElement(interrupt, "value")
        el.text = str(target_irqno)

    return peripheral


def _generate_section_register(registers: Element, window: MemoryMap, resource_info: ResourceInfo):
    resource: amaranth_soc.csr.bus.Element = resource_info.resource
    assert type(resource) == amaranth_soc.csr.bus.Element
    from amaranth_soc.csr.bus import Element

    register = SubElement(registers, "register")
    el = SubElement(register, "name")
    el.text = "_".join(resource_info.name)
    el = SubElement(register, "description")
    if hasattr(resource_info, "desc"):
        description = resource_info.desc
    else:
        description = "{} {} register".format(
            window.name,
            "_".join(resource_info.name),
        )
    el.text = description
    el = SubElement(register, "addressOffset")
    el.text = "0x{:04x}".format(resource_info.start)
    el = SubElement(register, "size")
    el.text = "{:d}".format((resource_info.end - resource_info.start) * 8) # TODO
    el = SubElement(register, "resetValue")
    el.text = "0x00" # TODO - calculate from fields ?

    el = SubElement(register, "access")
    access: Element.Access = resource.access
    access = "read-only" if access is Element.Access.R  else "write-only" if access is Element.Access.W else "read-write"
    el.text = access


    return register


def _generate_section_field(fields: Element, window: MemoryMap, resource_info: ResourceInfo):
    resource: amaranth_soc.csr.bus.Element = resource_info.resource
    assert type(resource) == amaranth_soc.csr.bus.Element

    logging.debug("Generating register field for window: {} resource_info: {}  resource: {} width: {}".format(
        window.name,
        resource_info.name,
        resource_info.resource.name,
        resource_info.resource.width
    ))

    field =  SubElement(fields, "field")
    el = SubElement(field, "name")
    el.text = resource.name
    el = SubElement(field, "description")
    if hasattr(resource, "desc"):
        description = resource.desc
    else:
        description = "{} {} register field".format(
            window.name,
            resource.name,
        )
    el.text = description
    el = SubElement(field, "bitRange")
    el.text = "[{:d}:0]".format(resource.width - 1)

    return field
