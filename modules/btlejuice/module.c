#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "hashmap.h"
#include "malloc.h"

static bool is_scanning = 0;

void CONN_INIT_CALLBACK(test)(metrics_t * metrics) {
  if(!metrics->local_device->gap_role != PERIPHERAL) {
    return;
  }
  if(!is_scanning) {
    start_scan();
    is_scanning = 1;
  }
}

int btlejuice_detected = 0;
void SCAN_CALLBACK(btlejuice)(metrics_t * metrics) {
  if(is_scanning && metrics->current_packet->valid && get_adv_packet_type() == ADV_IND) {
    bool same = 1;
    uint8_t i = 0;

    while(same && i < 6) {
      same = metrics->remote_device->address[i] == metrics->local_device->address[i];
      i++;
    }

    if(same) {
      btlejuice_detected = 1;
      log(metrics->remote_device->address,6);
      stop_scan();
    }

  }
}
