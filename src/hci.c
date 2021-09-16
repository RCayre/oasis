#include "hci.h"
#include "functions.h"

void launch_hci_command(uint16_t opcode, uint8_t * buffer) {
  void (*handler)(uint8_t * buffer) = *(uint32_t *)(hci_table + (opcode << 3) - 8);
  handler(buffer);
}

void start_scan() {
  uint8_t buffer[20];
  for(int i = 0; i < 20; i++) {
    buffer[i] = 0;
  }
  buffer[12] = 1;
  launch_hci_command(0xc, buffer);
}

void stop_scan() {
  uint8_t buffer[13];
  buffer[12] = 0;
  launch_hci_command(0xc, buffer);
}
