#include "hooks.h"

#include "log.h"
#include "functions.h"
#include "metrics.h"
#include "hashmap.h"
#include "malloc.h"

#define TIMESTAMP_HASHMAP_SIZE 16
#define TIMESTAMP_HASHMAP_TIMEOUT 5000000

extern metrics_t metrics;

extern uint8_t scan_callbacks_size;
extern callback_t scan_callbacks[];

static hashmap_t * timestamp_hashmap = NULL;

static bool mutex = 0;

static bool check_timeout(void * data) {
  uint32_t current_timestamp = get_timestamp_in_us();
  return (current_timestamp - *(uint32_t *)data) > TIMESTAMP_HASHMAP_TIMEOUT;
}

void process_scan_rx_header() {

}

void process_scan_rx() {
  metrics.scan_rx_done = is_rx_done();

  if(metrics.scan_rx_done && mutex == 0) { 
    mutex = 1;

    copy_header(metrics.scan_rx_frame_header);
    metrics.scan_rx_frame_size = metrics.scan_rx_frame_header[1];
    metrics.scan_rx_frame_pdu_type = metrics.scan_rx_frame_header[0] & 0xF;

    if(metrics.scan_rx_frame_pdu_type == 0) {
      // Get our own addr
      copy_own_adv_addr(metrics.own_addr);

      // Get the RSSI
      metrics.scan_rx_rssi = get_rssi();
      // Get the channel
      metrics.scan_rx_channel = get_channel();

      // Get the buffer
      copy_buffer(metrics.scan_rx_frame_payload, metrics.scan_rx_frame_size);
      // Get the Adv Address (first 6 bytes)
      memcpy(metrics.scan_rx_frame_adv_addr, metrics.scan_rx_frame_payload, 6);

      // Initialize the timestamp hashmap if it hasn't been initialized yet
      if(timestamp_hashmap == NULL) {
        timestamp_hashmap = hashmap_initialize(TIMESTAMP_HASHMAP_SIZE, check_timeout, 6);
      }

      uint32_t current_timestamp = get_timestamp_in_us(); 
      // Get the previous timestamp for this address
      void * previous_timestamp = hashmap_get(timestamp_hashmap, metrics.scan_rx_frame_adv_addr);
      if(previous_timestamp == NULL) {
        // Add the timestamp to the hashmap
        // We need to allocate memory as the hashmap takes ownership of the data
        uint32_t * current_timestamp_ptr = (uint32_t *) malloc(sizeof(uint32_t));
        *current_timestamp_ptr = current_timestamp;
        hashmap_put(timestamp_hashmap, metrics.scan_rx_frame_adv_addr, current_timestamp_ptr);
        metrics.scan_rx_frame_interval = -1;
      } else {
        // Compute the frame interval
        metrics.scan_rx_frame_interval = current_timestamp - *(uint32_t *)previous_timestamp;

        log(metrics.scan_rx_frame_adv_addr, &metrics.scan_rx_frame_interval, 4);

        // Save the new timestamp
        *(uint32_t *)previous_timestamp = current_timestamp;
      }

      //for(int i = 0; i < scan_callbacks_size; i++) {
      //  scan_callbacks[i](&metrics);
      //}
    }

    mutex = 0;
  }
}

void process_scan_delete() {
  hashmap_free(&timestamp_hashmap);
}
