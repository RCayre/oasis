MEMORY
{
	lowrom (rwx) : ORIGIN = 0x210400, LENGTH = 0x1010
/*	midrom (rwx) : ORIGIN = 0x218000, LENGTH = 0xb18 */
  midrom (rwx) : ORIGIN = 0x218f50, LENGTH = 0x1000
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
