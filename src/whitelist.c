#include "whitelist.h"


uint8_t whitelisted_device1[6] = {0x52, 0x24, 0x14, 0x4D, 0x00, 0xEA};
uint8_t whitelisted_device2[6] = {0xE3, 0x47, 0x91, 0xEA, 0xDA, 0x74};

uint8_t* whitelist[2] = {
  whitelisted_device1,
  whitelisted_device2
};

bool is_in_whitelist(uint8_t* address) {
  bool same = 0;
  for (int i=0;i<2;i++) {
    same = 1;
    for (int x=0;x<6;x++) {
      if (address[x] != whitelist[i][x]) {
        same = 0;
        break;
      }
    }
    if (same) break;
  }
  return same;
}
