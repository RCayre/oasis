MEMORY
{
	lowrom (rwx) : ORIGIN = 0x220900, LENGTH = 0xf43
	midrom (rwx) : ORIGIN = 0x213e14, LENGTH = 0x1000
}


SECTIONS {
  .rodata : {
  } > lowrom 

	.bss : {
	} > lowrom 

	.data : {
	} > lowrom 

	.text : {
	} > lowrom

  .bss.memory : {
  } > midrom
}
