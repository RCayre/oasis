#include "functions.h"
#include "hooks.h"
#include "log.h"

#define RAM_DATA_START (void*)0x20006000
#define DATA_START (void*)0x1e350
#define CODE_START (void*)0x20000

#define NOT_CONNECTED 0
#define CONNECTED_MASTER 1
#define CONNECTED_SLAVE 2

void * _memcpy(void * dst, void * src, uint32_t size);
void * bt_hci_event_create(uint8_t opcode, uint8_t size);
void * net_buf_simple_add(void * evt, uint8_t size);
void bt_recv(void *evt);
void hci_driver_send(void *evt);
bool radio_crc_is_valid();
int32_t radio_rssi_get();
uint32_t sys_clock_tick_get();
uint8_t radio_is_done();
uint8_t ll_addr_set(uint8_t addr_type, uint8_t *bdaddr);

/**
 * Registers
 */
uint32_t * rx_buffer_ptr = (uint32_t *)0x40001504;
uint32_t * frequency_ptr = (uint32_t *)0x40001508;
uint32_t * radio_state = (uint32_t *)0x40001550;

uint32_t * timer2_mode = (uint32_t *)0x4000a504;
uint32_t * timer2_width = (uint32_t *)0x4000a508;
uint32_t * timer2_prescaler = (uint32_t *)0x4000a510;
uint32_t * timer2_intenclr = (uint32_t *)0x4000a308;
uint32_t * timer2_clear = (uint32_t *)0x4000a00c;
uint32_t * timer2_start = (uint32_t *)0x4000a000;
uint32_t * timer2_capture1 = (uint32_t *)0x4000a044;
uint32_t * timer2_cc1 = (uint32_t *)0x4000a544;

void timer2_init() {
  *timer2_mode = 0;
	*timer2_width = 3;
	*timer2_prescaler = 4;

  *timer2_intenclr = (0xfff << 16);

  *timer2_clear = 1;
  *timer2_start = 1;
}

/**
 * Hooks
 */

void on_init() {
  memcpy(RAM_DATA_START, DATA_START, (uint32_t)CODE_START - (uint32_t)DATA_START);
  timer2_init();
}

void on_main() {
	uint8_t addr[] = {0x66,0x55,0x44,0x33,0x22,0x11};
	ll_addr_set(0,addr);
}

int connected = NOT_CONNECTED;
uint32_t access_address = 0x00000000;
uint32_t crc_init = 0x00000000;
uint16_t hop_interval = 0x0000;
uint8_t channel_map[5];

void on_setup_master_conn(void *rx, void *ftr, void *lll) {

	connected = CONNECTED_MASTER;
	// Copy access address
	memcpy(&access_address, lll+4, 4);
	// Copy CRC Init
	memcpy(&crc_init, lll+8, 4);
	// Copy Hop Interval
	memcpy(&hop_interval, lll+14, 2);
	// Copy channel map
	memcpy(&channel_map, lll+24, 5);

	process_conn_init();
}

void on_setup_slave_conn(void *rx, void *ftr, void *lll) {
	connected = CONNECTED_SLAVE;
	// Copy access address
	memcpy(&access_address, lll+4, 4);
	// Copy CRC Init
	memcpy(&crc_init, lll+8, 4);
	// Copy Hop Interval
	memcpy(&hop_interval, lll+14, 2);
	// Copy channel map
	memcpy(&channel_map, lll+24, 5);

	process_conn_init();
}

void on_cleanup_master_conn() {
	if (connected != NOT_CONNECTED) {
		process_conn_delete();
		connected = NOT_CONNECTED;
	}
}

void on_scan() {
  process_scan_rx_header();
  process_scan_rx();
}

void on_conn_tx(uint32_t *cb) {
		process_conn_tx();
}

void on_conn_rx() {
	process_conn_rx_header();
  process_conn_rx(1);
}


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
  bt_recv(evt);
}

uint32_t get_timestamp_in_us() {
  *timer2_capture1 = 1UL;
	return *timer2_cc1;
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
  uint8_t channel = 0;
  uint32_t frequency = *(uint32_t*)frequency_ptr;
  if (frequency == 2) channel = 37;
  else if (frequency == 26) channel = 38;
  else if (frequency == 80) channel = 39;
  else if (frequency < 24) channel = (frequency/2) - 2;
  else channel = (frequency/2) - 3;
  return channel;
}

void copy_buffer(uint8_t * dst, uint8_t size) {
  memcpy(dst, (void*)(*rx_buffer_ptr + 2), size);
}

bool is_slave() {
  return connected == CONNECTED_SLAVE;
}

void copy_channel_map(uint8_t * dst) {
	memcpy(dst,&channel_map, 5);
}

uint16_t get_hop_interval() {
  return hop_interval;
}

uint32_t get_crc_init() {
  return crc_init;
}

void copy_access_addr(uint8_t * dst) {
	memcpy(dst, &access_address, 4);
}

bool is_crc_good() {
  return radio_crc_is_valid();
}

void launch_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size) {

}
