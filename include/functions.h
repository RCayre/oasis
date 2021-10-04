#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

void * memcpy(void *dst, void* src, uint32_t size);
void send_hci(uint8_t opcode, void * content, uint32_t size);
uint32_t get_timestamp_in_us();
int get_rssi();
void copy_header(uint8_t * dst);
bool is_rx_done();
void copy_own_adv_addr(uint8_t * dst);
uint8_t get_channel();
void copy_buffer(uint8_t * dst, uint8_t size);
bool is_slave();
void copy_channel_map(uint8_t * dst);
uint16_t get_hop_interval();
uint32_t get_crc_init();
void copy_access_addr(uint8_t * dst);
bool is_crc_good();
void launch_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size);

#endif
