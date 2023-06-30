OUTPUT_FORMAT("elf32-littleriscv")
OUTPUT_ARCH("riscv")
ENTRY(_start)

REGION_ALIAS("ram", scratchpad)

SECTIONS
{
    . = 0x00000000;

    /* Start of day code. */
    .init :
    {
        *(.init) *(.init.*)
    } > rom
    .text :
    {
        *(.text) *(.text.*)
    } > rom

    .rodata :
    {
        *(.rodata) *(.rodata.*)
    } > rom
    .sdata :
    {
        PROVIDE(__global_pointer$ = .);
        *(.sdata) *(.sdata.*)
    } > ram
    .data :
    {
        *(.data) *(.data.*)
    } > ram
    .bss :
    {
        *(.bss) *(.bss.*)
    } > ram

}

PROVIDE(__stack_top = ORIGIN(ram) + LENGTH(ram));
