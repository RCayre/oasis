/* Explorer la gestion de la pile pour pouvoir nous réservrer une zone RAM */
MEMORY
{
  /* flash data between 0x23050 and flash */
	flash (rwx) : ORIGIN = 0x24048, LENGTH = 0x2000
    ram (rwx) : ORIGIN = 0x20002A80, LENGTH = 0x1000
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
