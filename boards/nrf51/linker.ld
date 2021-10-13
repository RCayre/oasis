/* Explorer la gestion de la pile pour pouvoir nous réservrer une zone RAM */
MEMORY
{
  /* flash data between 0x23050 and flash */
	flash (rwx) : ORIGIN = CODE_START, LENGTH = CODE_LENGTH
  ram (rwx) : ORIGIN = RAM_START, LENGTH = RAM_LENGTH
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
