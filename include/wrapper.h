#ifndef WRAPPER_H
#define WRAPPER_H

#include "types.h"

void * memcpy(void *dst, void* src, uint32_t size);

uint32_t get_timestamp_in_us();
uint32_t now();

int get_rssi();
bool is_crc_good();
void copy_header(uint8_t * dst);
bool is_rx_done();
void copy_buffer(uint8_t * dst, uint8_t size);
uint8_t get_channel();
void copy_own_bd_addr(uint8_t * dst);
uint8_t get_current_gap_role();

#ifdef CONNECTION_ENABLED
bool is_slave();
void copy_channel_map(uint8_t * dst);
uint16_t get_hop_interval();
uint32_t get_crc_init();
void copy_access_addr(uint32_t * dst);
#endif

void start_scan();
void stop_scan();
void log(uint8_t *buffer, uint8_t size);

#endif
