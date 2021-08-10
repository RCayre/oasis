#include "hci.h"

void on_conn() {
	uint32_t data = 0x11223344;
	send_hci(0xFF,(uint8_t*)&data, 4);
}
