#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "hashmap.h"
#include "malloc.h"
#include "alert.h"

#define KNOB_ALERT_NUMBER 6

void CONN_RX_CALLBACK(knob)(metrics_t * metrics) {
  // If the received packet is a pairing request with a low entropy value
  if (get_packet_size() >= 11 &&
      get_llid() == 2 && // L2CAP
      metrics->current_packet->content[2] == 0x06 && metrics->current_packet->content[3] == 0x00 && // CID = 6 <-> SecurityManager
      metrics->current_packet->content[4] == 0x01 && // Pairing Request
      metrics->current_packet->content[8] <= 10
  ) {
    // Raise an alert
    alert(KNOB_ALERT_NUMBER,(uint8_t*)&metrics->current_packet->content[8], 1);
  }
}
