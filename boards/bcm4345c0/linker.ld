MEMORY
{
	lowrom (rwx) : ORIGIN = 0x210200, LENGTH = 0xa3e
	midrom (rwx) : ORIGIN = 0xd8200, LENGTH = 0x500
	highrom (rwx) : ORIGIN = 0x218355, LENGTH = 0x47a
}


SECTIONS {
  .rodata : {
  } > highrom

	.bss : {
	} > highrom 

	.data : {
	} > highrom 

	.text : {
	} > lowrom

  .bss.memory : {
  } > midrom
}
