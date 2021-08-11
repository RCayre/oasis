#include "hci.h"

#include "log.h"
#include "functions.h"
#include "metrics.h"

extern metrics_t metrics;

extern uint8_t conn_callbacks_size;
extern callback_t conn_callbacks[];

void on_conn_header() {
  uint32_t ptr = lm_getRawRssiWithTaskId();
  uint8_t addr[6] = { 0x31, 0x32, 0x33, 0x34, 0x35, 0x36 };
  log(addr, &ptr, 4);
}

void on_conn(void * ptr) {
  uint8_t addr[6] = { 0x11, 0x12, 0x13, 0x14, 0x15, 0x16 };
  log(addr, &ptr, 4);

  for(int i = 0; i < conn_callbacks_size; i++) {
    conn_callbacks[i](&metrics);
  }
}
