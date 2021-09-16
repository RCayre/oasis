#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "log.h"
#include "hashmap.h"
#include "malloc.h"

#define HASHMAP_SIZE 16

typedef struct btlejack_data {
  uint32_t crc_counter;
  bool is_init;
} btlejack_data_t;

static hashmap_t * hashmap = NULL;

void CONN_CALLBACK(btlejack)(metrics_t * metrics) {
  if(hashmap == NULL) {
    hashmap = hashmap_initialize(HASHMAP_SIZE, NULL, 4);
  }

  // Get this device's data for detecting a mitm attack
  btlejack_data_t * data;
  void * ret = hashmap_get(hashmap, metrics->conn_access_addr);
  if(ret == NULL) {
    // Add an entry if it wasn't found
    data = (btlejack_data_t *) malloc(sizeof(btlejack_data_t));
    data->crc_counter = 0;
    data->is_init = 0;
    int err = hashmap_put(hashmap, metrics->conn_access_addr, data);
    // If there was not enough memory, skip
    if(err == -1) {
      return;
    }
  } else {
    data = (btlejack_data_t*)ret; 
  }

  if(!data->is_init) {
    data->is_init = 1;
    log(metrics->conn_access_addr, &metrics->conn_crc_init, 4);
  }

  data->crc_counter += !metrics->conn_rx_crc_good;
  if(data->crc_counter > 3) {
    log(NULL, "BTLEJACK", 8);
  }

  if(metrics->conn_rx_crc_good) {
    data->crc_counter = 0;
  }
}
