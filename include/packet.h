#ifndef PACKET_H
#define PACKET_H

#include "types.h"

typedef enum address_type {
  PUBLIC = 0,
  RANDOM = 1
} address_type_t;

typedef enum adv_type {
  ADV_IND = 0,
  ADV_DIRECT_IND = 1,
  ADV_NONCONN_IND = 2,
  SCAN_REQ = 3,
  SCAN_RSP = 4,
  CONNECT_REQ = 5,
  ADV_SCAN_IND = 6
}
adv_type_t;

typedef struct packet {
  uint32_t timestamp;
  uint16_t valid;
  uint16_t channel;
  uint16_t rssi;
  uint8_t header[2];
  uint8_t content[255];
} packet_t;

typedef struct adv_ind {
  uint8_t adv_address[6];
  uint8_t *data;
} adv_ind_t;

uint8_t get_packet_size();

#ifdef SCAN_ENABLED
adv_type_t get_adv_packet_type();
adv_ind_t* get_adv_ind_dissector();

address_type_t get_tx_address_type();
address_type_t get_rx_address_type();
#endif

#ifdef CONNECTION_ENABLED
uint8_t get_llid();
#endif

#endif
