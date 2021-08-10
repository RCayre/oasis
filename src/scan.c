#include "hci.h"

void on_scan() {
	uint32_t data = 0x41424344;
	send_hci(0xFF,(uint8_t*)&data,4);
}
