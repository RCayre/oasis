#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

// These registers are only accessible through memcpybt8
extern uint8_t * rx_header;
extern uint8_t * rx_buffer;
extern uint8_t * status;
extern uint8_t * channel;

extern uint8_t IS_SLAVE_OFFSET;
extern uint8_t CHANNEL_MAP_OFFSET;
extern uint8_t SECOND_STRUCT_OFFSET;
extern uint8_t CRC_INIT_OFFSET_IN_SECOND_STRUCT;
extern uint8_t ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT;

void * memcpy(void *dst, void* src, uint32_t size);

void * memcpybt8(void* dst, void* src, uint32_t size);

void send_hci(uint8_t opcode, void * content, uint32_t size);

uint32_t get_timestamp_in_us();

int get_rssi();

#endif
