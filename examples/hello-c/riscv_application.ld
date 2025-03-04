OUTPUT_FORMAT("elf32-littleriscv")
OUTPUT_ARCH("riscv")
ENTRY(_start)

SECTIONS
{
    . = ORIGIN(blockram);

    /* Start of day code. */
    .init :
    {
        *(.init) *(.init.*)
    } > blockram
    .text :
    {
        *(.text) *(.text.*)
    } > blockram

    .rodata :
    {
        *(.rodata) *(.rodata.*)
    } > blockram
    .sdata :
    {
        PROVIDE(__global_pointer$ = .);
        *(.sdata) *(.sdata.*)
    }
    .data :
    {
        *(.data) *(.data.*)
    } > blockram
    .bss :
    {
        *(.bss) *(.bss.*)
    } > blockram

}

PROVIDE(__stack_top = ORIGIN(blockram) + LENGTH(blockram));
