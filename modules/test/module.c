#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "wrapper.h"

#define OPCODE_TEST_TIME 0x00
#define OPCODE_TEST_RX_SCAN 0x01
#define OPCODE_TEST_INIT_CONN 0x02
#define OPCODE_TEST_RX_CONN 0x03

void TIME_CALLBACK(test)(metrics_t * metrics) {
  uint8_t message[12];
  message[0] = OPCODE_TEST_TIME;
  uint32_t timestamp = now();
  memcpy(message+1,&timestamp,4);
  memcpy(message+5,metrics->local_device->address,6);
  message[11] = metrics->local_device->gap_role;
  log(message, 12);
}

void SCAN_CALLBACK(test)(metrics_t * metrics) {
  uint8_t message[13+get_packet_size()];
  message[0] = OPCODE_TEST_RX_SCAN;
  memcpy(message+1, &metrics->current_packet->timestamp,4);
  memcpy(message+5, &metrics->current_packet->valid,2);
  memcpy(message+7, &metrics->current_packet->channel,2);
  memcpy(message+9, &metrics->current_packet->rssi,2);
  memcpy(message+11, &metrics->current_packet->header,2);
  memcpy(message+13, &metrics->current_packet->content,get_packet_size());

  log(message,13+get_packet_size());
}


void CONN_INIT_CALLBACK(test)(metrics_t * metrics) {
  uint8_t message[16];
  message[0] = OPCODE_TEST_INIT_CONN;
  memcpy(message+1,&metrics->current_connection->access_address, 4);
  memcpy(message+5,&metrics->current_connection->crc_init, 4);
  memcpy(message+9,&metrics->current_connection->hop_interval, 2);
  memcpy(message+11,metrics->current_connection->channel_map, 5);
  log(message,16);
}

void CONN_RX_CALLBACK(test)(metrics_t * metrics) {
  uint8_t message[13+get_packet_size()];
  message[0] = OPCODE_TEST_RX_CONN;
  memcpy(message+1, &metrics->current_packet->timestamp,4);
  memcpy(message+5, &metrics->current_packet->valid,2);
  memcpy(message+7, &metrics->current_packet->channel,2);
  memcpy(message+9, &metrics->current_packet->rssi,2);
  memcpy(message+11, &metrics->current_packet->header,2);
  memcpy(message+13, &metrics->current_packet->content,get_packet_size());

  log(message,13+get_packet_size());
}
