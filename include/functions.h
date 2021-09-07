#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

// These registers are only accessible through memcpybt8
extern uint8_t * rx_header;
extern uint8_t * rx_buffer;
extern uint8_t * status;
extern uint8_t * channel;

void * memcpy(void *dst, void* src, uint32_t size);

void * memcpybt8(void* dst, void* src, uint32_t size);

void send_hci(uint8_t opcode, void * content, uint32_t size);

uint32_t get_timestamp_in_us();

int get_rssi();

#endif
