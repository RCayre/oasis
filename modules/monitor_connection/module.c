#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "wrapper.h"
#include "monitor.h"
#include "messages.h"

void CONN_INIT_CALLBACK(monitor_connection)(metrics_t * metrics) {
  uint8_t message[17];
  message[0] = MESSAGE_TYPE_MONITOR;
  message[1] = OPCODE_MONITOR_INIT_CONN;
  memcpy(message+2,&metrics->current_connection->access_address, 4);
  memcpy(message+6,&metrics->current_connection->crc_init, 4);
  memcpy(message+10,&metrics->current_connection->hop_interval, 2);
  memcpy(message+12,metrics->current_connection->channel_map, 5);
  log(message,17);
}

void CONN_RX_CALLBACK(monitor_connection)(metrics_t * metrics) {
  uint8_t message[14+get_packet_size()];
  message[0] = MESSAGE_TYPE_MONITOR;
  message[1] = OPCODE_MONITOR_RX_CONN;
  memcpy(message+2, &metrics->current_packet->timestamp,4);
  memcpy(message+6, &metrics->current_packet->valid,2);
  memcpy(message+8, &metrics->current_packet->channel,2);
  memcpy(message+10, &metrics->current_packet->rssi,2);
  memcpy(message+12, &metrics->current_packet->header,2);
  memcpy(message+14, &metrics->current_packet->content,get_packet_size());

  log(message,14+get_packet_size());
}
