#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "log.h"
#include "hashmap.h"
#include "malloc.h"

#define WINDOW_SIZE 36
#define HASHMAP_SIZE 16

typedef struct circ_buffer {
  uint32_t buf[WINDOW_SIZE];
  uint8_t cur;
  bool is_init;
} circ_buffer_t;

typedef struct injectable_data {
  circ_buffer_t window;
  uint32_t threshold;
  bool under_attack;
} injectable_data_t;

static hashmap_t * hashmap = NULL;

void CONN_CALLBACK(injectable)(metrics_t * metrics) {
  if(hashmap == NULL) {
    hashmap = hashmap_initialize(HASHMAP_SIZE, NULL, 4);
  }

  // Get this device's data for detecting a mitm attack
  injectable_data_t * data;
  void * ret = hashmap_get(hashmap, metrics->conn_access_addr);
  if(ret == NULL) {
    // Add an entry if it wasn't found
    data = (injectable_data_t *) malloc(sizeof(injectable_data_t));
    data->window.cur = 0;
    data->window.is_init = 0;
    data->threshold = 0;
    data->under_attack = 0;
    int err = hashmap_put(hashmap, metrics->conn_access_addr, data);
    // If there was not enough memory, skip
    if(err == -1) {
      return;
    }
  } else {
    data = (injectable_data_t*)ret; 
  }

  // Exclude first value
  if(metrics->conn_rx_frame_interval == -1) {
    return;
  }

  data->window.buf[data->window.cur] = metrics->conn_rx_frame_interval;

  log(metrics->conn_rx_frame_header, &metrics->conn_rx_frame_interval, 4);

  // If the window has been entirely filled
  if(!data->window.is_init && data->window.cur == WINDOW_SIZE - 1) {
    data->window.is_init = 1; 
//    log(metrics->conn_access_addr, "GOOD", 4);
  }

  data->window.cur += 1;
  data->window.cur %= WINDOW_SIZE;

  if(data->window.is_init) {
    uint32_t mean = 0;
    for(int i = 0; i < WINDOW_SIZE; i++) {
      mean += data->window.buf[i];
    }
    mean /= WINDOW_SIZE;


    uint32_t interval = metrics->conn_rx_frame_interval;
    if(interval > mean + 10 || interval < mean - 10) {
      log(metrics->conn_access_addr, "INJECTABLE", 8);
    }

  }
}

