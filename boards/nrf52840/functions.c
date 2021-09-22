#include "functions.h"
#include "hooks.h"
#include "log.h"

#define RAM_DATA_START (void*)0x20006000
#define DATA_START (void*)0x1e350
#define CODE_START (void*)0x20000

void * _memcpy(void * dst, void * src, uint32_t size);
void * bt_hci_event_create(uint8_t opcode, uint8_t size);
void * net_buf_simple_add(void * evt, uint8_t size);
void bt_recv_prio(void *evt);
bool radio_crc_is_valid();
int32_t radio_rssi_get();
uint32_t sys_clock_tick_get();
uint8_t radio_is_done();

/**
 * Hooks
 */

void on_init() {
  memcpy(RAM_DATA_START, DATA_START, (uint32_t)CODE_START - (uint32_t)DATA_START); 
}

void on_scan() {
  uint32_t t = *(uint32_t*)0x3d09000;
  log(NULL, &t, 4);
//  process_scan_rx_header();
//  process_scan_rx();
}

void on_conn() {
//  process_conn_rx_header();
//  process_conn_rx(); 
}

/**
 * Registers
 */
uint32_t * rx_buffer_ptr = (uint32_t *)0x40001504;

/**
 * API implementation
 */

void * memcpy(void * dst, void * src, uint32_t size) {
  return _memcpy(dst, src, size);
}

void send_hci(uint8_t opcode, void * content, uint32_t size) {
  void * evt = bt_hci_event_create(opcode, size);
  uint8_t * buf = net_buf_simple_add(evt+8, size);
  memcpy(buf, content, size);
  bt_recv_prio(evt);
}

uint32_t get_timestamp_in_us() {
  return sys_clock_tick_get();
}

int get_rssi() {
  return radio_rssi_get();
}

void copy_header(uint8_t * dst) {
  memcpy(dst, (void*)*rx_buffer_ptr, 2);
}

bool is_rx_done() {
  return (radio_is_done() & 0xFF) != 0;
}

void copy_own_adv_addr(uint8_t * dst) {
}

uint8_t get_channel() {
  return 0;
}

void copy_buffer(uint8_t * dst, uint8_t size) {
  memcpy(dst, (void*)(*rx_buffer_ptr + 2), size);
}

bool is_slave() {
  return 0;
}

void copy_channel_map(uint8_t * dst) {
}

uint8_t get_hop_interval() {
  return 0;
}

uint32_t get_crc_init() {
  return 0;
}

void copy_access_addr(uint8_t * dst) {
}

bool is_crc_good() {
  return radio_crc_is_valid();
}

void launch_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size) {

}