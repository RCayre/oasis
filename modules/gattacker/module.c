#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "packet.h"
#include "hashmap.h"
#include "malloc.h"
#include "whitelist.h"
#include "alert.h"

#define GATTACKER_ALERT_NUMBER 3

#define MAX_ADV_DELAY 10000

#define WINDOW_SIZE 32
#define HASHMAP_SIZE 16
#define HASHMAP_TIMEOUT 1000

typedef struct circ_buffer {
  uint32_t buf[WINDOW_SIZE];
  uint8_t cur;
  bool is_init;
} circ_buffer_t;

typedef struct gattacker_data {
  circ_buffer_t window;
  uint8_t last_channel;
  uint32_t threshold;
  int under_attack;
  uint32_t last_timestamp;
} gattacker_data_t;

static hashmap_t * gattacker_hashmap = NULL;

bool check_to_remove(void* entry) {
  gattacker_data_t* data = (gattacker_data_t*)entry;
  return ((now() - data->last_timestamp) > 1000000*5);
}
void SCAN_CALLBACK(gattacker)(metrics_t * metrics) {
  // Check if a packet was received
  if(get_adv_packet_type() == ADV_IND && is_in_whitelist(metrics->remote_device->address)) {

    if(gattacker_hashmap == NULL) {
      gattacker_hashmap = hashmap_initialize(HASHMAP_SIZE,NULL, 6);
    }

    // Get this device's data for detecting a gattacker attack
    gattacker_data_t * data;
    void * ret = hashmap_get(gattacker_hashmap, metrics->remote_device->address);
    if(ret == NULL) {
      // Add an entry if it wasn't found
      data = (gattacker_data_t *) malloc(sizeof(gattacker_data_t));
      data->window.cur = 0;
      data->window.is_init = 0;
      data->last_channel = 0;
      data->threshold = 0;
      data->under_attack = 0;
      data->last_timestamp = 0;
      int err = hashmap_put(gattacker_hashmap, metrics->remote_device->address, data);
      // If there was not enough memory, skip
      if(err == -1) {
        return;
      }
    } else {
      data = (gattacker_data_t*)ret;
    }

    // Store the last timestamp for timeout purposes
    data->last_timestamp = now();

    // Exclude first value
    if(metrics->remote_device->advertisements_interval == 0) {
      return;
    }

    // Exclude values after a channel switch
    if(data->last_channel == 0) {
      data->last_channel = metrics->current_packet->channel;
    } else if(data->last_channel != metrics->current_packet->channel) {
      data->last_channel = metrics->current_packet->channel;
      return;
    }

    /*********************************************************/
    /*        Compute an estimate of the adv interval        */
    /*********************************************************/

    // add to the window
    data->window.buf[data->window.cur] = metrics->remote_device->advertisements_interval;

    // If the window has been entirely filled
    if(!data->window.is_init && data->window.cur == WINDOW_SIZE - 1) {
      data->window.is_init = 1;
    }

    data->window.cur += 1;
    data->window.cur %= WINDOW_SIZE;

    // Compute the min of the window if the window has been filled once
    if(data->window.is_init) {
      uint32_t min = data->window.buf[0];
      for(uint8_t i = 1; i < WINDOW_SIZE; i++) {
        uint32_t val = data->window.buf[i];
        if(val < min) {
          min = val;
        }
      }

      min /= 625;
      min *= 625;

      /*********************************************************/
      /*        Compute a threshold for the adv interval       */
      /*********************************************************/
      if(!data->threshold || min > data->threshold + MAX_ADV_DELAY) {
        data->threshold = min - MAX_ADV_DELAY;
      }
      if (metrics->remote_device->address[0] == 0x52) {
        uint8_t buf[8];
        memcpy(buf, &min, 4);
        memcpy(buf+4, &data->threshold, 4);
        alert(0x41, buf, 8);
      }
      /*********************************************************/
      /*                 Detect a MITM attack                  */
      /*********************************************************/

      if(min < data->threshold) {
        // If we go below the threshold
        data->under_attack += 1;
        if (data->under_attack > 50) {
          alert(GATTACKER_ALERT_NUMBER, metrics->remote_device->address,6);
        }
      } else if(data->under_attack) {
        // If we were under attack and we go above the threshold
        data->under_attack = 0;
      }
    }
  }
}
