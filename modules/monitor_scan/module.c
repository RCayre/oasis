#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "wrapper.h"
#include "monitor.h"
#include "messages.h"

void SCAN_CALLBACK(monitor_scan)(metrics_t * metrics) {
  uint8_t message[14+get_packet_size()];
  message[0] = MESSAGE_TYPE_MONITOR;
  message[1] = OPCODE_MONITOR_RX_SCAN;
  memcpy(message+2, &metrics->current_packet->timestamp,4);
  memcpy(message+6, &metrics->current_packet->valid,2);
  memcpy(message+8, &metrics->current_packet->channel,2);
  memcpy(message+10, &metrics->current_packet->rssi,2);
  memcpy(message+12, &metrics->current_packet->header,2);
  memcpy(message+14, &metrics->current_packet->content,get_packet_size());

  log(message,14+get_packet_size());
}
