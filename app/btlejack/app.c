#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "log.h"
#include "hashmap.h"
#include "malloc.h"

void CONN_CALLBACK(btlejack)(metrics_t * metrics) {
  log(NULL, &metrics->conn_rx_crc_good, 1);
}
