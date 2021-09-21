#include "functions.h"

#define RAM_DATA_START (void*)0x20006000
#define DATA_START (void*)0x1e350
#define CODE_START (void*)0x1f500

void * _memcpy(void * dst, void * src, uint32_t size);

/**
 * Board specific hook
 */

void on_init() {
  memcpy(RAM_DATA_START, DATA_START, (uint32_t)CODE_START - (uint32_t)DATA_START); 
}

/**
 * API implementation
 */

void * memcpy(void * dst, void * src, uint32_t size) {
  return _memcpy(dst, src, size);
}

void * memcpybt8(void * dst, void * src, uint32_t size) {
  return NULL;
}

void send_hci(uint8_t opcode, void * content, uint32_t size) {
}

uint32_t get_timestamp_in_us() {
  return 0;
}

int get_rssi() {
  return 0;
}

/**
 * API registers
 */

uint8_t * rx_header = (uint8_t *) 0x318B98;
uint8_t * rx_buffer = (uint8_t *) 0x370C00;
uint8_t * status = (uint8_t *) 0x318BAC;
uint8_t * channel = (uint8_t *) 0x283356;

uint8_t IS_SLAVE_OFFSET = 15;
uint8_t CHANNEL_MAP_OFFSET = 116;
uint8_t SECOND_STRUCT_OFFSET = 80;
//uint8_t HOP_INTERVAL_STRUCT_OFFSET = 34;
//uint8_t SLAVE_LATENCY_STRUCT_OFFSET = 35;
uint8_t CRC_INIT_OFFSET_IN_SECOND_STRUCT = 0;
uint8_t ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT = 52;

uint8_t * hci_table = (uint8_t *) 0x143ea8;

uint8_t * own_addr = (uint8_t *) 0x280ca4;
