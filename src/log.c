#include "log.h"

#include "malloc.h"
#include "hci.h"
#include "functions.h"

void log(uint8_t * addr, void* arg, int size) {
  // 0xAA + header + addr + data
  uint32_t buffer_size = 2 + 6 + size;
  uint8_t * buffer = (uint8_t *) malloc(buffer_size);

  // Set header as 1 if there is an address
  uint8_t header = 0;
  if(addr != NULL) {
    header = 1;
  }

  buffer[0] = 0xAA;
  buffer[1] = header;
  if(addr != NULL) {
    memcpy(buffer+2, addr, 6);
  }
  memcpy(buffer+8, arg, size);

  send_hci(0xFF, buffer, buffer_size);
  free(buffer);
}
