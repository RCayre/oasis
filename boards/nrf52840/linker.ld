MEMORY
{
  /* flash data between 0x1e350 and flash */
	flash (rwx) : ORIGIN = 0x20000, LENGTH = 0x1000
  ram (rwx) : ORIGIN = 0x20006000, LENGTH = 0x1500
}

SECTIONS {
	.text : {
	} > flash 

  .rodata : {
  } > flash 

	.data : {
	} > ram 

	.bss : {
	} > ram 

  .bss.memory : {
  } > ram
}
