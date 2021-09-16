#include "functions.h"

/**
 * Functions needed to implement the api
 */

void * _memcpy(void * dst, void * src, uint32_t size);
void * _memcpybt8(void * dsr, void * src, uint32_t size);
char * bthci_event_AllocateEventAndFillHeader(uint8_t len_total, char event_code, uint8_t len_data);
void bthci_event_AttemptToEnqueueEventToTransport(char * event);
int lm_getRawRssiWithTaskId();
void btclk_GetNatClk_clkpclk(uint32_t * t);
uint32_t btclk_Convert_clkpclk_us(uint32_t * p);

/**
 * API implementation
 */

void * memcpy(void * dst, void * src, uint32_t size) {
  return _memcpy(dst, src, size);
}

void * memcpybt8(void * dst, void * src, uint32_t size) {
  return _memcpybt8(dst, src, size);
}

void send_hci(uint8_t opcode, void * content, uint32_t size) {
	char *hci_buffer = bthci_event_AllocateEventAndFillHeader(size + 2, opcode, size);
	memcpy(hci_buffer + 10, content, size);
  bthci_event_AttemptToEnqueueEventToTransport(hci_buffer);
}

uint32_t get_timestamp_in_us() {
  uint32_t t[2];
  btclk_GetNatClk_clkpclk(t);
  return btclk_Convert_clkpclk_us(t);
}

int get_rssi() {
  return lm_getRawRssiWithTaskId();
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
