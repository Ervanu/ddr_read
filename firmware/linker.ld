INCLUDE generated/output_format.ld
ENTRY(_start)

__DYNAMIC = 0;

INCLUDE generated/regions.ld

SECTIONS
{
	.text :
	{
		_ftext = .;
		/* ARM (Quicklogic EOS-S3, Gowin EMCU) interrupt vector tables use section name "isr_vector" */
		/* - such a table has to be placed at start */
		KEEP(*(.isr_vector))		
		/* Make sure crt0 files come first, and they, and the isr */
		/* don't get disposed of by greedy optimisation */
		*crt0*(.text)
		KEEP(*crt0*(.text))
		KEEP(*(.text.isr))

		*(.text .stub .text.* .gnu.linkonce.t.*)
		_etext = .;
	} > main_ram_app

	.rodata :
	{
		. = ALIGN(8);
		_frodata = .;
		*(.rodata .rodata.* .gnu.linkonce.r.*)
		*(.rodata1)
		*(.got .got.*)
		*(.toc .toc.*)
		FILL(0);
		. = ALIGN(8);
		_erodata = .;
	} > main_ram_app

	.data :
	{
		. = ALIGN(8);
		_fdata = .;
		*(.data .data.* .gnu.linkonce.d.*)
		*(.data1)
		_gp = ALIGN(16);
		*(.sdata .sdata.* .gnu.linkonce.s.*)
		FILL(0);
		. = ALIGN(8);
		_edata = .;
	} > sram AT > main_ram_app

	.bss :
	{
		. = ALIGN(8);
		_fbss = .;
		*(.dynsbss)
		*(.sbss .sbss.* .gnu.linkonce.sb.*)
		*(.scommon)
		*(.dynbss)
		*(.bss .bss.* .gnu.linkonce.b.*)
		*(COMMON)
		. = ALIGN(8);
		_ebss = .;
		_end = .;
	} > sram

	/DISCARD/ :
	{
		*(.eh_frame)
		*(.comment)
	}	
}

PROVIDE(_fstack = ORIGIN(sram) + LENGTH(sram));

PROVIDE(_fdata_rom = LOADADDR(.data));
PROVIDE(_edata_rom = LOADADDR(.data) + SIZEOF(.data));
