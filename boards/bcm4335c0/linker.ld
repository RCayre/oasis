MEMORY
{
	lowrom (rwx) : ORIGIN = 0x20de94, LENGTH = 0xd43
	midrom (rwx) : ORIGIN = 0xd7500, LENGTH = 0x500
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
