#include "log.h"

#include "hci.h"
#include "functions.h"
#include "metrics.h"
#include "hashmap.h"
#include "malloc.h"

#define TIMESTAMP_HASHMAP_SIZE 16
#define TIMESTAMP_HASHMAP_TIMEOUT 1000

extern metrics_t metrics;

extern uint8_t scan_callbacks_size;
extern callback_t scan_callbacks[];

// These registers are only accessible through memcpybt8
static uint8_t * rx_header = (uint8_t *) 0x318B98;
static uint8_t * rx_buffer = (uint8_t *) 0x370C00;
static uint8_t * status = (uint8_t *) 0x318BAC;
static uint8_t * channel = (uint8_t *) 0x283356;

static hashmap_t * timestamp_hashmap = NULL;

static bool mutex = 0;

static bool check_timeout(void * data) {
  uint32_t current_timestamp = clock_SystemTimeMicroseconds32_nolock();
  return (current_timestamp - *(uint32_t *) data) > TIMESTAMP_HASHMAP_TIMEOUT; 
}

void on_scan_header() {
  memcpybt8(metrics.scan_rx_frame_header, rx_header, 2);
  metrics.scan_rx_frame_size = metrics.scan_rx_frame_header[1];
  metrics.scan_rx_frame_pdu_type = metrics.scan_rx_frame_header[0] & 0xF;
}

void on_scan() {
  metrics.scan_status = *status;
  metrics.scan_rx_done = metrics.scan_status & 0x4;

  if(metrics.scan_rx_done && metrics.scan_rx_frame_pdu_type == 0 && mutex == 0) {
    mutex = 1;

    // Get the RSSI
    metrics.scan_rx_rssi = lm_getRawRssiWithTaskId();
    // Get the channel
    metrics.scan_rx_channel = *channel;

    // Get the buffer
    memcpybt8(metrics.scan_rx_frame, rx_buffer, metrics.scan_rx_frame_size);
    // Get the Adv Address (first 6 bytes)
    memcpy(metrics.scan_rx_frame_adv_addr, metrics.scan_rx_frame, 6);

    // Initialize the timestamp hashmap if it hasn't been initialized yet
    if(timestamp_hashmap == NULL) {
      timestamp_hashmap = hashmap_initialize(TIMESTAMP_HASHMAP_SIZE, check_timeout);
    }

    uint32_t current_timestamp = clock_SystemTimeMicroseconds32_nolock();
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

      // Save the new timestamp
      *(uint32_t *)previous_timestamp = current_timestamp;
    }

    for(int i = 0; i < scan_callbacks_size; i++) {
      scan_callbacks[i](&metrics);
    }

    mutex = 0;
  }
}
