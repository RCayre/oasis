#include "hci.h"

#include "log.h"

void on_conn(void * ptr) {
  uint8_t addr[6] = { 0x11, 0x12, 0x13, 0x14, 0x15, 0x16 };
  log(addr, &ptr, 4);
}
