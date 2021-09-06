MEMORY
{
	lowrom (rwx) : ORIGIN = 0x210300, LENGTH = 0xF00
/*	midrom (rwx) : ORIGIN = 0x218000, LENGTH = 0xb18 */
  midrom (rwx) : ORIGIN = 0x218f50, LENGTH = 0x3080
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
