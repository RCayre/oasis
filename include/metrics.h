#ifndef METRICS_H
#define METRICS_H

#include "types.h"

typedef struct metrics {
  uint8_t own_addr[6];

  /* SCAN */
  uint16_t scan_status;
  bool scan_rx_done;

  uint32_t scan_rx_frame_interval;
  uint32_t scan_tx_rx_frame_interval;

  uint8_t scan_rx_frame_header[2];
  uint8_t scan_rx_frame_size;
  uint8_t scan_rx_frame_pdu_type;

  uint8_t scan_rx_frame_payload[255];
  uint8_t scan_rx_frame_adv_addr[6];

  int32_t scan_rx_rssi;
  uint8_t scan_rx_channel;

  /* CONN */
  uint8_t conn_channel_map[5];
  uint32_t conn_crc_init;
  uint8_t conn_access_addr[4];
  uint32_t conn_rx_frame_interval;
  bool conn_rx_crc_good;
  uint8_t conn_rx_frame_header[2];
  uint8_t conn_rx_frame_size;
  uint8_t conn_rx_frame_payload[43];
  uint8_t slave_latency;
  uint16_t hop_interval;
  bool is_slave;

	uint32_t rx_counter;
	uint32_t tx_counter;
	uint32_t last_counter_interval;
	uint32_t consecutive_missed_packets;


} metrics_t;

#endif
