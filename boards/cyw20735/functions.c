#include "functions.h"
#include "hooks.h"
#include "malloc.h"

// This is the parameter of the conn callback
void * conn_param;

/**
 * Hooks
 */
void on_scan_header() {
  process_scan_rx_header();
}

void on_scan() {
  process_scan_rx();
}

void on_scan_delete() {
  process_scan_delete();
}

void on_conn_header() {
  process_conn_rx_header();
}

void on_conn(void * ptr) {
  conn_param = ptr;
  process_conn_rx();
}

void on_conn_delete(void * ptr) {
  conn_param = ptr;
  process_conn_delete();
}

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
 * Registers and constants needed to implement the api
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

void copy_header(uint8_t * dst) {
  memcpybt8(dst, rx_header, 2);
}

bool is_rx_done(uint8_t status) {
  return *status & 0x4;
}

void copy_own_adv_addr(uint8_t * dst) {
  memcpy(dst, own_addr, 6);
}

uint8_t get_channel() {
  return *channel;
}

void copy_buffer(uint8_t * dst, uint8_t size) {
  memcpybt8(dst, rx_buffer, size);
}

bool is_slave() {
  return *(uint8_t *)(conn_param + IS_SLAVE_OFFSET) != 0;
}

void copy_channel_map(uint8_t * dst) {
  memcpy(dst, conn_param + CHANNEL_MAP_OFFSET, 6);
}

uint8_t get_hop_interval() {
//  return *(uint8_t *)(conn_param + HOP_INTERVAL_STRUCT_OFFSET);
  return 0;
}

uint32_t get_crc_init() {
  // Pointer to the second structure 
  void * p = *(void**)(conn_param + SECOND_STRUCT_OFFSET);
  return *(uint32_t*)(p + CRC_INIT_OFFSET_IN_SECOND_STRUCT);
}

void copy_access_addr(uint8_t * dst) {
  // Pointer to the second structure 
  void * p = *(void**)(conn_param + SECOND_STRUCT_OFFSET);
  memcpy(dst, p + ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT, 4);
}

bool is_crc_good() {
  return (*status & 0x2) == 2;
}

void launch_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size) {
  uint8_t * param = (uint8_t *) malloc(size + 11);
  // Set first 11 bytes to 0
  for(uint8_t i = 0; i < 12; i++) {
    param[i] = 0;
  }
  // Copy the hci command parameter
  memcpy(param + 12, buffer, size); 

  void (*handler)(uint8_t * buffer) = *(uint32_t *)(hci_table + (opcode << 3) - 8);
  handler(param);
}
