#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "hashmap.h"
#include "malloc.h"

#define DETECTION_INTERVAL 5
uint32_t interval;
uint32_t channel_watched[3];
uint32_t number_of_packets[3];
uint32_t continuous_jamming_detected;

void SCAN_CALLBACK(jamming)(metrics_t * metrics) {
  if (metrics->current_packet->valid) {
    number_of_packets[metrics->current_packet->channel - 37]++;
  }
  channel_watched[metrics->current_packet->channel - 37] = 1;
}

void TIME_CALLBACK(jamming)(metrics_t * metrics) {
  if (metrics->local_device->gap_role == SCANNER) {
    interval++;

    if ((interval % DETECTION_INTERVAL) == 0) {
      //log((uint8_t*)number_of_packets,4*3);
      if (number_of_packets[0] == 0 && !channel_watched[0]) { continuous_jamming_detected = 37; log((uint8_t*)&continuous_jamming_detected,4);}
      if (number_of_packets[1] == 0 && !channel_watched[1]) {continuous_jamming_detected = 38; log((uint8_t*)&continuous_jamming_detected,4);}
      if (number_of_packets[2] == 0 && !channel_watched[2]) {continuous_jamming_detected = 39; log((uint8_t*)&continuous_jamming_detected,4);}

      number_of_packets[0] = 0;
      number_of_packets[1] = 0;
      number_of_packets[2] = 0;

      channel_watched[0] = 0;
      channel_watched[1] = 0;
      channel_watched[2] = 0;
    }
    else {
      uint32_t channel = get_channel();
      if (channel == 37 || channel == 38 || channel == 39) {
        channel_watched[channel-37] = 1;
      }
    }
  }
  else {
    number_of_packets[0] = 0;
    number_of_packets[1] = 0;
    number_of_packets[2] = 0;

    channel_watched[0] = 0;
    channel_watched[1] = 0;
    channel_watched[2] = 0;

    interval = 0;
  }
}
