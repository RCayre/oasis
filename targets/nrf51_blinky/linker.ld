
MEMORY
{
    code (rwx) : ORIGIN = CODE_START, LENGTH = CODE_SIZE
    data (rwx) : ORIGIN = DATA_START, LENGTH = DATA_SIZE
}


SECTIONS {
    .text : {
    } > code

    .rodata : {
    } > code

    .data : {
    } > data

    .bss : {
    } > data

    .bss.memory : {
    } > data
}

