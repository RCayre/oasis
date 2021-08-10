#ifndef HCI_H
#define HCI_H
#include "functions.h"

void send_hci(uint8_t opcode, uint8_t *content, uint32_t size);

#endif
