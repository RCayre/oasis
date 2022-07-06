#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "wrapper.h"
#include "monitor.h"
#include "messages.h"

void TIME_CALLBACK(monitor_time)(metrics_t * metrics) {
  uint8_t message[13];
  message[0] = MESSAGE_TYPE_MONITOR;
  message[1] = OPCODE_MONITOR_TIME;
  uint32_t timestamp = now();
  memcpy(message+2,&timestamp,4);
  memcpy(message+6,metrics->local_device->address,6);
  message[12] = metrics->local_device->gap_role;
  log(message, 13);
}
