#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "wrapper.h"



void TIME_CALLBACK(test)(metrics_t * metrics) {
  uint32_t timestamp = now();
  log((uint8_t*)&timestamp, 4);
}


void SCAN_CALLBACK(test)(metrics_t * metrics) {
  uint8_t buffer[255];
  memcpy(buffer, metrics->current_packet->header,2);
  memcpy(buffer+2, metrics->current_packet->content,get_packet_size());
  log(buffer,2+get_packet_size());
}


void CONN_RX_CALLBACK(test)(metrics_t * metrics) {
  uint8_t buffer[255];
  memcpy(buffer, metrics->current_packet->header,2);
  memcpy(buffer+2, metrics->current_packet->content,get_packet_size());
  log(buffer,2+get_packet_size());
}
