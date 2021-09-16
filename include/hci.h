#ifndef HCI_H
#define HCI_H

#include "types.h"

void launch_hci_command(uint16_t opcode, uint8_t * buffer);

void start_scan();
void stop_scan();

#endif
