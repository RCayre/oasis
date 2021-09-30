#include "hooks.h"

#include "log.h"
#include "functions.h"
#include "metrics.h"
#include "hashmap.h"
#include "malloc.h"
#include "hci.h"

#define TIMESTAMP_HASHMAP_SIZE 16

extern metrics_t metrics;

extern uint8_t conn_callbacks_size;
extern callback_t conn_callbacks[];

static hashmap_t * timestamp_hashmap = NULL;

static uint32_t current_timestamp;

void process_conn_rx_header() {
  current_timestamp = get_timestamp_in_us();
}

void process_conn_rx() {

  if(timestamp_hashmap == NULL) {
    timestamp_hashmap = hashmap_initialize(TIMESTAMP_HASHMAP_SIZE, NULL, 4);
  }

  metrics.is_slave = is_slave();
  copy_channel_map(metrics.conn_channel_map);
  metrics.hop_interval = get_hop_interval();
  metrics.conn_crc_init = get_crc_init();
  copy_access_addr(metrics.conn_access_addr);

  copy_header(metrics.conn_rx_frame_header);
  metrics.conn_rx_frame_size = metrics.conn_rx_frame_header[1];

  copy_buffer(metrics.conn_rx_frame_payload, metrics.conn_rx_frame_size);

  // Check if the CRC is good
  metrics.conn_rx_crc_good = is_crc_good();

  // Get the previous timestamp for this address
  void * previous_timestamp = hashmap_get(timestamp_hashmap, metrics.conn_access_addr);
  if(previous_timestamp == NULL) {
    // Add the timestamp to the hashmap
    // We need to allocate memory as the hashmap takes ownership of the data
    uint32_t * current_timestamp_ptr = (uint32_t *) malloc(sizeof(uint32_t));
    *current_timestamp_ptr = current_timestamp;
    hashmap_put(timestamp_hashmap, metrics.conn_access_addr, current_timestamp_ptr);
    metrics.conn_rx_frame_interval = -1;
  } else {
    if(current_timestamp == *(uint32_t *) previous_timestamp) {
      // The header hook was not called
      metrics.conn_rx_frame_interval = -1;
    } else {
      // Compute the frame interval
      metrics.conn_rx_frame_interval = current_timestamp - *(uint32_t *)previous_timestamp;

      // Save the new timestamp
      *(uint32_t *)previous_timestamp = current_timestamp;
    }
  }
	log(NULL,&metrics.conn_rx_frame_interval,4);
  //for(int i = 0; i < conn_callbacks_size; i++) {
  //  conn_callbacks[i](&metrics);
  //}
}

void process_conn_delete() {
  uint8_t access_addr[4];
  copy_access_addr(access_addr);

  // Cleanup this connection
  hashmap_delete(timestamp_hashmap, access_addr);
}
