#ifndef CONNECTION_H
#define CONNECTION_H

#include "types.h"

typedef struct connection {
  uint32_t access_address;
  uint32_t crc_init;
  uint16_t hop_interval;
  uint16_t packets_lost_counter;
  uint16_t tx_counter;
  uint16_t rx_counter;
  uint8_t channel_map[5];
} connection_t;

#endif
