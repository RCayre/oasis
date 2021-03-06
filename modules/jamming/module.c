#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "hashmap.h"
#include "malloc.h"
#include "alert.h"

#define JAMMING_ALERT_NUMBER 5
#define DETECTION_INTERVAL 5

uint32_t interval;
uint32_t number_of_packets[3];

void SCAN_CALLBACK(jamming)(metrics_t * metrics) {
  if (metrics->current_packet->valid) {
    number_of_packets[metrics->current_packet->channel - 37]++;
  }
}

void TIME_CALLBACK(jamming)(metrics_t * metrics) {
  if (metrics->local_device->gap_role == SCANNER) {
    interval++;

    if ((interval != 0 && interval % DETECTION_INTERVAL) == 0) {
      if (number_of_packets[0] == 0) {
        uint32_t continuous_jamming_detected = 37;
        alert(JAMMING_ALERT_NUMBER,(uint8_t*)&continuous_jamming_detected,4);
      }
      if (number_of_packets[1] == 0) {
        uint32_t continuous_jamming_detected = 38;
        alert(JAMMING_ALERT_NUMBER,(uint8_t*)&continuous_jamming_detected,4);
      }
      if (number_of_packets[2] == 0) {
        uint32_t continuous_jamming_detected = 39;
        alert(JAMMING_ALERT_NUMBER,(uint8_t*)&continuous_jamming_detected,4);
      }

      number_of_packets[0] = 0;
      number_of_packets[1] = 0;
      number_of_packets[2] = 0;
    }

  }
  else {
    number_of_packets[0] = 0;
    number_of_packets[1] = 0;
    number_of_packets[2] = 0;

    interval = 0;
  }
}
