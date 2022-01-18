#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "hashmap.h"
#include "malloc.h"

uint32_t knob = 0;
void CONN_RX_CALLBACK(knob)(metrics_t * metrics) {

  if (get_packet_size() >= 11 &&
      get_llid() == 2 && // L2CAP
      metrics->current_packet->content[2] == 0x06 && metrics->current_packet->content[3] == 0x00 && // CID = 6 <-> SecurityManager
      metrics->current_packet->content[4] == 0x01 && // Pairing Request
      metrics->current_packet->content[8] <= 10
  ) {
    knob = 1;
    log((uint8_t*)&knob, 4);
    knob = 0;
  }
}
