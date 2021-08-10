MEMORY
{
	lowrom (rwx) : ORIGIN = 0x210500, LENGTH = 0xF00
	midrom (rwx) : ORIGIN = 0x218000, LENGTH = 0xF00
}


SECTIONS {
  .rodata : {
  } > lowrom 

	.data : {
	} > lowrom 

	.text : {
	} > lowrom
	
	.bss : {
	} > midrom
}
