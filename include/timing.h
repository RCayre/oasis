#ifndef TIMING_H
#define TIMING_H

#ifdef TIMING_MEASUREMENT

#include "types.h"
#include "messages.h"
#include "wrapper.h"

#define SCAN_EVENT          0
#define TIME_EVENT          1
#define CONN_TX_EVENT       2
#define CONN_RX_EVENT       3
#define CONN_INIT_EVENT     4
#define CONN_DELETE_EVENT   5

#define event_type_t uint8_t

typedef struct timing_measures {
  uint32_t scan_timestamp_start;
  uint32_t scan_timestamp_end;
  uint32_t scan_timestamp_callbacks;

  uint32_t time_timestamp_start;
  uint32_t time_timestamp_end;
  uint32_t time_timestamp_callbacks;

  uint32_t conn_rx_timestamp_start;
  uint32_t conn_rx_timestamp_end;
  uint32_t conn_rx_timestamp_callbacks;

  uint32_t conn_tx_timestamp_start;
  uint32_t conn_tx_timestamp_end;
  uint32_t conn_tx_timestamp_callbacks;

  uint32_t conn_init_timestamp_start;
  uint32_t conn_init_timestamp_end;
  uint32_t conn_init_timestamp_callbacks;

  uint32_t conn_delete_timestamp_start;
  uint32_t conn_delete_timestamp_end;
  uint32_t conn_delete_timestamp_callbacks;
} timing_measures_t;

void report_timestamps(event_type_t type);
#endif

#endif
