#include "events.h"
#include "wrapper.h"
#include "metrics.h"
#include "hashmap.h"
#include "malloc.h"
#include "timing.h"

#ifdef SCAN_ENABLED

#define TIMESTAMP_HASHMAP_SIZE 16
#define TIMESTAMP_HASHMAP_TIMEOUT 5000000

#ifdef TIMING_MEASUREMENT
extern timing_measures_t timing_measures;
#endif

extern metrics_t metrics;

extern uint8_t scan_callbacks_size;
extern callback_t scan_callbacks[];

static hashmap_t * scan_timestamp_hashmap = NULL;


static bool check_timeout(void * data) {
  uint32_t current_timestamp = now();
  return (current_timestamp - *(uint32_t *)data) > TIMESTAMP_HASHMAP_TIMEOUT;
}


void process_scan_rx_header() {
    packet_t* current_packet = metrics.current_packet;
    current_packet->timestamp = get_timestamp_in_us();
    copy_header(current_packet->header);
}
uint32_t frame_interval = 0;

void process_scan_rx() {
    // TODO: add gap role to remote device
    // TODO: add address to remote device (from connection ?)
    #ifdef TIMING_MEASUREMENT
    timing_measures.scan_timestamp_start = now();
    #endif

    local_device_t* local_device = metrics.local_device;
    copy_own_bd_addr(local_device->address);
    local_device->gap_role = (gap_role_t)get_current_gap_role();

    packet_t* current_packet = metrics.current_packet;
    current_packet->channel = get_channel();
    current_packet->valid = is_crc_good();

    current_packet->rssi = get_rssi();

    if (current_packet->valid) {
      copy_buffer(current_packet->content,get_packet_size());
      if (get_adv_packet_type() == ADV_IND) {
        adv_ind_t* dissector = get_adv_ind_dissector();


        memcpy(metrics.remote_device->address,dissector->adv_address,6);
        metrics.remote_device->address_type = get_tx_address_type();
        #ifdef INTERVAL_ESTIMATION_ENABLED
        if(scan_timestamp_hashmap == NULL) {
          scan_timestamp_hashmap = hashmap_initialize(TIMESTAMP_HASHMAP_SIZE, NULL, 6);
        }
        uint32_t* previous_timestamp = hashmap_get(scan_timestamp_hashmap, dissector->adv_address);
        if(previous_timestamp == NULL) {
          // Add the timestamp to the hashmap
          // We need to allocate memory as the hashmap takes ownership of the data
          uint32_t * current_timestamp_ptr = (uint32_t *) malloc(sizeof(uint32_t));
          *current_timestamp_ptr = current_packet->timestamp;
          int err = hashmap_put(scan_timestamp_hashmap, dissector->adv_address, current_timestamp_ptr);
          metrics.remote_device->advertisements_interval = 0;
        } else {
          // Compute the frame interval
          metrics.remote_device->advertisements_interval = current_packet->timestamp - *(uint32_t *)previous_timestamp;
          // Save the new timestamp
          *(uint32_t *)previous_timestamp = current_packet->timestamp;
        }
        #endif
      }
    }
    #ifdef TIMING_MEASUREMENT
    timing_measures.scan_timestamp_callbacks = now();
    #endif

    for(int i = 0; i < scan_callbacks_size; i++) {
      scan_callbacks[i](&metrics);
    }

    #ifdef TIMING_MEASUREMENT
    timing_measures.scan_timestamp_end = now();
    report_timestamps(SCAN_EVENT);
    #endif
}
#endif
