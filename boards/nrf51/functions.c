#include "functions.h"
#include "hooks.h"
#include "log.h"

#define RAM_DATA_START (void*)0x20002A80
#define DATA_START (void*)0x23048
#define CODE_START (void*)0x24048

/**
 * Hooks
 */

void on_init() {
  memcpy(RAM_DATA_START, DATA_START, (uint32_t)CODE_START - (uint32_t)DATA_START);
}

/**
 * API implementation
 */

void * memcpy(void * dst, void * src, uint32_t size) {
	for (int i=0;i<size;i++) {
		dst[i] = src[i];
	}
}

void send_hci(uint8_t opcode, void * content, uint32_t size) {
}

uint32_t get_timestamp_in_us() {
    return 0;
}

int get_rssi() {
    return 0;
}

void copy_header(uint8_t * dst) {
}

bool is_rx_done() {
    return 0;
}

void copy_own_adv_addr(uint8_t * dst) {
}

uint8_t get_channel() {
    return 0;
}

void copy_buffer(uint8_t * dst, uint8_t size) {
}

bool is_slave() {
  return 0;
}

void copy_channel_map(uint8_t * dst) {
}

uint16_t get_hop_interval() {
  return 0;
}

uint32_t get_crc_init() {
  return 0;
}

void copy_access_addr(uint8_t * dst) {
}

bool is_crc_good() {
  return 0;
}

void launch_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size) {

}
