#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "log.h"
#include "hashmap.h"
#include "malloc.h"
#include "hci.h"

static bool is_scanning = 0;

void CONN_CALLBACK(btlejuice)(metrics_t * metrics) {
  if(!metrics->is_slave) {
    return; 
  }

  if(!is_scanning) {
    start_scan(); 
    is_scanning = 1;
  }
}

void SCAN_CALLBACK(btlejuice)(metrics_t * metrics) {
  if(is_scanning) {
    bool same = 1;
    uint8_t i = 0;
    while(same && i < 6) {
      same = metrics->scan_rx_frame_adv_addr[i] == metrics->own_addr[i];
      i++;
    }

    if(same) {
      log(NULL, "BTLEJUICE", 9);
    }
  }
}
