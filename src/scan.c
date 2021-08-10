#include "log.h"

#include "hci.h"

void on_scan() {
  uint32_t data = 0x41424344;
  uint8_t addr[6] = { 0x1, 0x2, 0x3, 0x4, 0x5, 0x6 };
  log(addr, &data, 4);
}
