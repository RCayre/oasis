#ifndef HCI_H
#define HCI_H

#include "types.h"

void send_hci(uint8_t opcode, void *content, uint32_t size);

#endif
