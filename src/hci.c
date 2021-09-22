#include "hci.h"
#include "functions.h"


void start_scan() {
  uint8_t buffer[2];
  buffer[0] = 1;
  buffer[1] = 0;
  launch_hci_command(0xc, buffer, 2);
}

void stop_scan() {
  uint8_t buffer[2];
  buffer[0] = 1;
  buffer[1] = 0;
  launch_hci_command(0xc, buffer, 2);
}
