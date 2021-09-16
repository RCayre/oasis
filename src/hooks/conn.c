#include "log.h"
#include "functions.h"
#include "metrics.h"
#include "hashmap.h"
#include "malloc.h"

#define TIMESTAMP_HASHMAP_SIZE 16

extern metrics_t metrics;

extern uint8_t conn_callbacks_size;
extern callback_t conn_callbacks[];

static hashmap_t * timestamp_hashmap = NULL;

static uint32_t current_timestamp;

void on_conn_header() {
  current_timestamp = get_timestamp_in_us(); 
}

void on_conn(void * ptr) {
  if(timestamp_hashmap == NULL) {
    timestamp_hashmap = hashmap_initialize(TIMESTAMP_HASHMAP_SIZE, NULL, 4);
  }

  metrics.is_slave = *(uint8_t *)(ptr + IS_SLAVE_OFFSET) != 0;
  memcpy(metrics.conn_channel_map, ptr + CHANNEL_MAP_OFFSET, 6);
//  metrics.slave_latency = *(uint8_t *)(ptr + SLAVE_LATENCY_STRUCT_OFFSET);
//  metrics.hop_interval = *(uint8_t *)(ptr + HOP_INTERVAL_STRUCT_OFFSET);
  // Pointer to the second structure 
  void * p = *(void**)(ptr + SECOND_STRUCT_OFFSET);
  metrics.conn_crc_init = *(uint32_t*)(p + CRC_INIT_OFFSET_IN_SECOND_STRUCT);
  memcpy(metrics.conn_access_addr, p + ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT, 4);

  uint8_t header[2];
  memcpybt8(header, rx_header, 2);
  memcpy(metrics.conn_rx_frame_header, header, 2);
  metrics.conn_rx_frame_size = header[1];

  uint8_t buffer[40];
  memcpybt8(buffer, rx_buffer, metrics.conn_rx_frame_size);
  memcpy(metrics.conn_rx_frame_payload, buffer, metrics.conn_rx_frame_size);

  // Check if the CRC is good
  metrics.conn_rx_crc_good = (*status & 0x2) == 2;

  log(NULL, &metrics.is_slave, 1);

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

//  for(int i = 0; i < conn_callbacks_size; i++) {
//    conn_callbacks[i](&metrics);
//  }
}
