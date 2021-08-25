#include "hci.h"

#include "log.h"
#include "functions.h"
#include "metrics.h"

#define CHANNEL_MAP_OFFSET 116
#define SECOND_STRUCT_OFFSET 80
#define CRC_INIT_OFFSET_IN_SECOND_STRUCT 0
#define ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT 52

extern metrics_t metrics;

extern uint8_t conn_callbacks_size;
extern callback_t conn_callbacks[];

// These registers are only accessible through memcpybt8
static uint8_t * status = (uint8_t *) 0x318BAC;

void on_conn_header() {
}

void on_conn(void * ptr) {
  memcpy(metrics.conn_channel_map, ptr + CHANNEL_MAP_OFFSET, 6);
  // Pointer to the second structure 
  void * p = *(void**)(ptr + SECOND_STRUCT_OFFSET);
  metrics.conn_crc_init = *(uint32_t*)(p + CRC_INIT_OFFSET_IN_SECOND_STRUCT);
  metrics.conn_access_addr = *(uint32_t*)(p + ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT);

  // Check if the CRC is good
  metrics.conn_rx_crc_good = (*status & 0x2) == 2;

  for(int i = 0; i < conn_callbacks_size; i++) {
    conn_callbacks[i](&metrics);
  }
}
