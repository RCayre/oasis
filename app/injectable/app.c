#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "log.h"
#include "hashmap.h"
#include "malloc.h"

#define WINDOW_SIZE 24
#define HASHMAP_SIZE 16
#define THRESHOLD 100

typedef struct circ_buffer {
  uint32_t buf[WINDOW_SIZE];
  uint8_t cur;
  uint8_t skipped_windows;
} circ_buffer_t;

typedef struct injectable_data {
  circ_buffer_t window;
  uint8_t last_hop_interval;
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
    data->window.skipped_windows = 0;
    data->last_hop_interval = 0;
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

  // We want to reset the window if there is a connection update
  if((data->last_hop_interval != 0) && (data->last_hop_interval != metrics->hop_interval)) {
    data->window.skipped_windows = 0;
    data->window.cur = 0;
    data->last_hop_interval = metrics->hop_interval;
    return;
  }

  data->last_hop_interval = metrics->hop_interval;

  if(data->window.skipped_windows < 1) {
    data->window.buf[data->window.cur] = metrics->conn_rx_frame_interval;

    // If the window has been entirely filled
    if(data->window.cur == WINDOW_SIZE - 1) {
      data->window.skipped_windows += 1; 
    }

    data->window.cur += 1;
    data->window.cur %= WINDOW_SIZE;
  } else {
    uint32_t min = data->window.buf[0];
    for(int i = 1; i < WINDOW_SIZE; i++) {
      uint32_t v = data->window.buf[i];
      if(v < min) {
        min = v;
      }
    }

    uint32_t interval = metrics->conn_rx_frame_interval;
    log(NULL, &interval, 4);
    log(NULL, &min, 4);
    if(interval > min * (1 + metrics->slave_latency) + THRESHOLD) {
      log(&interval, "INJECTABLE", 9);
    } else {
      // We want to ignore the value if an attack has been detected
      data->window.buf[data->window.cur] = metrics->conn_rx_frame_interval;
      data->window.cur += 1;
      data->window.cur %= WINDOW_SIZE;
    }
  }
}

