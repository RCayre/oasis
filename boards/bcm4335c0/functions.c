#include "functions.h"

/**
 * Functions needed to implement the api
 */

void * _memcpy(void * dst, void * src, uint32_t size);
void * _memcpybt8(void * dst, void * src, uint32_t size);
char * bthci_event_AllocateEventAndFillHeader(char event_code, uint8_t len_total);
void bthci_event_AttemptToEnqueueEventToTransport(char * event);
void bthci_event_FreeEvent(char * event);
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
  char *hci_buffer = bthci_event_AllocateEventAndFillHeader(opcode, size + 2);
  memcpy(hci_buffer + 2, content, size);
  bthci_event_AttemptToEnqueueEventToTransport(hci_buffer); 
  bthci_event_FreeEvent(hci_buffer);
}

uint32_t get_timestamp_in_us() {
  uint32_t t[2];
  btclk_GetNatClk_clkpclk(t);
  return btclk_Convert_clkpclk_us(t);
}

int get_rssi() {
  return *(char *)0x32fc34 + *(char *)0x200f6f;
}

/**
 * API registers
 */

uint8_t * rx_header = (uint8_t *) 0x318B98;
uint8_t * rx_buffer = (uint8_t *) 0x370880;
uint8_t * status = (uint8_t *) 0x318BAC;
uint8_t * channel = (uint8_t *) 0x283356;
