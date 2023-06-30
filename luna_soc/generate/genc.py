#
# This file is part of LUNA.
#
# Copyright (c) 2023 Great Scott Gadgets <info@greatscottgadgets.com>
# SPDX-License-Identifier: BSD-3-Clause

"""Generate a C library for SoC designs."""

import datetime

from lambdasoc.soc.cpu       import CPUSoC


class GenC():

    def __init__(self, soc: CPUSoC):
        self._soc = soc


    # - generate c header -----------------------------------------------------

    def generate_c_header(self, macro_name="SOC_RESOURCES", file=None, platform_name="Generic Platform"):
        """ Generates a C header file that simplifies access to the platform's resources.

        Parameters:
            macro_name -- Optional. The name of the guard macro for the C header, as a string without spaces.
            file       -- Optional. If provided, this will be treated as the file= argument to the print()
                          function. This can be used to generate file content instead of printing to the terminal.
        """

        def emit(content):
            """ Utility function that emits a string to the targeted file. """
            print(content, file=file)

        # Create a mapping that maps our register sizes to C types.
        types_for_size = {
            4: 'uint32_t',
            2: 'uint16_t',
            1: 'uint8_t'
        }

        # Emit a warning header.
        emit("/*")
        emit(" * Automatically generated by LUNA; edits will be discarded on rebuild.")
        emit(" * (Most header files phrase this 'Do not edit.'; be warned accordingly.)")
        emit(" *")
        emit(f" * Generated: {datetime.datetime.now()}.")
        emit(" */")
        emit("\n")

        emit(f"#ifndef __{macro_name}_H__")
        emit(f"#define __{macro_name}_H__")
        emit("")
        emit("#include <stdint.h>\n")
        emit("#include <stdbool.h>")
        emit("")

        emit("//")
        emit("// Environment Information")
        emit("//")

        emit("")
        emit(f"#define PLATFORM_NAME \"{platform_name}\"")
        emit("")


        # Emit our constant data for all Minerva CPUs.
        self._emit_minerva_basics(emit)

        emit("//")
        emit("// Peripherals")
        emit("//")
        memory_map: amaranth_soc.memory.MemoryMap
        resource_info: amaranth_soc.memory.ResourceInfo
        for memory_map, resource_info, address, size in self._soc.resources():
            resource = resource_info.resource

            # Always generate a macro for the resource's ADDRESS and size.
            if memory_map.name is not None:
                name = "{}_{}".format(memory_map.name, "_".join(resource_info.name))
            else:
                name =  "_".join(resource_info.name)
            emit(f"#define {name.upper()}_ADDRESS (0x{address:08x}U)")
            emit(f"#define {name.upper()}_SIZE ({size})")

            # If we have information on how to access this resource, generate convenience
            # macros for reading and writing it.
            if hasattr(resource, 'access'):
                c_type = types_for_size[size]

                # Generate a read stub, if useful...
                if resource.access.readable():
                    emit(f"static inline {c_type} {name}_read(void) {{")
                    emit(f"    volatile {c_type} *reg = ({c_type} *){name.upper()}_ADDRESS;")
                    emit(f"    return *reg;")
                    emit(f"}}")

                # ... and a write stub.
                if resource.access.writable():
                    emit(f"static inline void {name}_write({c_type} value) {{")
                    emit(f"    volatile {c_type} *reg = ({c_type} *){name.upper()}_ADDRESS;")
                    emit(f"    *reg = value;")
                    emit(f"}}")

            emit("")


        emit("//")
        emit("// Interrupts")
        emit("//")
        for irq, peripheral in self._soc._interrupt_map.items():

            # Function that determines if a given unit has an IRQ pending.
            emit(f"static inline bool {peripheral.name}_interrupt_pending(void) {{")
            emit(f"    return pending_irqs() & (1 << {irq});")
            emit(f"}}")

            # IRQ masking
            emit(f"static inline void {peripheral.name}_interrupt_enable(void) {{")
            emit(f"    irq_setmask(irq_getmask() | (1 << {irq}));")
            emit(f"}}")
            emit(f"static inline void {peripheral.name}_interrupt_disable(void) {{")
            emit(f"    irq_setmask(irq_getmask() & ~(1 << {irq}));")
            emit(f"}}")

        emit("#endif")
        emit("")

    def _emit_minerva_basics(self, emit):
        """ Emits the standard Minerva RISC-V CSR functionality.

        Parameters
        ----------
        emit: callable(str)
            The function used to print the code lines to the output stream.
        """

        emit("#ifndef read_csr")
        emit("#define read_csr(reg) ({ unsigned long __tmp; \\")
        emit("  asm volatile (\"csrr %0, \" #reg : \"=r\"(__tmp)); \\")
        emit("  __tmp; })")
        emit("#endif")
        emit("")
        emit("#ifndef write_csr")
        emit("#define write_csr(reg, val) ({ \\")
        emit("  asm volatile (\"csrw \" #reg \", %0\" :: \"rK\"(val)); })")
        emit("#endif")
        emit("")
        emit("#ifndef set_csr")
        emit("#define set_csr(reg, bit) ({ unsigned long __tmp; \\")
        emit("  asm volatile (\"csrrs %0, \" #reg \", %1\" : \"=r\"(__tmp) : \"rK\"(bit)); \\")
        emit("  __tmp; })")
        emit("#endif")
        emit("")
        emit("#ifndef clear_csr")
        emit("#define clear_csr(reg, bit) ({ unsigned long __tmp; \\")
        emit("  asm volatile (\"csrrc %0, \" #reg \", %1\" : \"=r\"(__tmp) : \"rK\"(bit)); \\")
        emit("  __tmp; })")
        emit("#endif")
        emit("")

        emit("#ifndef MSTATUS_MIE")
        emit("#define MSTATUS_MIE         0x00000008")
        emit("#endif")
        emit("")

        emit("//")
        emit("// Minerva headers")
        emit("//")
        emit("")
        emit("static inline uint32_t irq_getie(void)")
        emit("{")
        emit("        return (read_csr(mstatus) & MSTATUS_MIE) != 0;")
        emit("}")
        emit("")
        emit("static inline void irq_setie(uint32_t ie)")
        emit("{")
        emit("        if (ie) {")
        emit("                set_csr(mstatus, MSTATUS_MIE);")
        emit("        } else {")
        emit("                clear_csr(mstatus, MSTATUS_MIE);")
        emit("        }")
        emit("}")
        emit("")
        emit("static inline uint32_t irq_getmask(void)")
        emit("{")
        emit("        return read_csr(0x330);")
        emit("}")
        emit("")
        emit("static inline void irq_setmask(uint32_t value)")
        emit("{")
        emit("        write_csr(0x330, value);")
        emit("}")
        emit("")
        emit("static inline uint32_t pending_irqs(void)")
        emit("{")
        emit("        return read_csr(0x360);")
        emit("}")
        emit("")


    # - generate linker script ------------------------------------------------

    def generate_ld_script(self, file=None):
        """ Generates an ldscript that holds our primary RAM and ROM regions.

        Parameters:
            file       -- Optional. If provided, this will be treated as the file= argument to the print()
                          function. This can be used to generate file content instead of printing to the terminal.
        """

        def emit(content):
            """ Utility function that emits a string to the targeted file. """
            print(content, file=file)


        # Insert our automatically generated header.
        emit("/**")
        emit(" * Linker memory regions.")
        emit(" *")
        emit(" * Automatically generated by LUNA; edits will be discarded on rebuild.")
        emit(" * (Most header files phrase this 'Do not edit.'; be warned accordingly.)")
        emit(" *")
        emit(f" * Generated: {datetime.datetime.now()}.")
        emit(" */")
        emit("")

        emit("MEMORY")
        emit("{")

        # TODO - whooboy this is 'orrible!
        # TODO - check all memories

        # Add regions for our main ROM and our main RAM.
        if self._soc.bootrom:
            start, size = self._soc.range_for_peripheral(self._soc.bootrom)
            if size:
                emit(f"    rom : ORIGIN = 0x{start:08x}, LENGTH = 0x{size:08x}")

        if self._soc.scratchpad:
            start, size = self._soc.range_for_peripheral(self._soc.scratchpad)
            if size:
                emit(f"    scratchpad : ORIGIN = 0x{start:08x}, LENGTH = 0x{size:08x}")

        if self._soc.mainram:
            start, size = self._soc.range_for_peripheral(self._soc.mainram)
            if size:
                emit(f"    ram : ORIGIN = 0x{start:08x}, LENGTH = 0x{size:08x}")

        emit("}")
        emit("")
