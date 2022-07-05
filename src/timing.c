#include "timing.h"
#include "wrapper.h"

timing_measures_t timing_measures;

void report_timestamps(event_type_t type) {
  uint32_t start = 0xFFFFFFFF;
  uint32_t end = 0xFFFFFFFF;
  uint32_t callbacks = 0xFFFFFFFF;

  if (type == SCAN_EVENT) {
    start = timing_measures.scan_timestamp_start;
    end = timing_measures.scan_timestamp_end;
    callbacks = timing_measures.scan_timestamp_callbacks;
  }
  else if (type == CONN_INIT_EVENT) {
    start = timing_measures.conn_init_timestamp_start;
    end = timing_measures.conn_init_timestamp_end;
    callbacks = timing_measures.conn_init_timestamp_callbacks;
  }
  else if (type == CONN_DELETE_EVENT) {
    start = timing_measures.conn_delete_timestamp_start;
    end = timing_measures.conn_delete_timestamp_end;
    callbacks = timing_measures.conn_delete_timestamp_callbacks;
  }
  else if (type == CONN_RX_EVENT) {
    start = timing_measures.conn_rx_timestamp_start;
    end = timing_measures.conn_rx_timestamp_end;
    callbacks = timing_measures.conn_rx_timestamp_callbacks;
  }
  else if (type == CONN_TX_EVENT) {
    start = timing_measures.conn_tx_timestamp_start;
    end = timing_measures.conn_tx_timestamp_end;
    callbacks = timing_measures.conn_tx_timestamp_callbacks;
  }
  else if (type == TIME_EVENT) {
    start = timing_measures.time_timestamp_start;
    end = timing_measures.time_timestamp_end;
    callbacks = timing_measures.time_timestamp_callbacks;
  }
  uint8_t timestamp_buffer[1+3*4];
  timestamp_buffer[0] = type;
  memcpy(&timestamp_buffer[1],&start, 4);
  memcpy(&timestamp_buffer[5],&callbacks, 4);
  memcpy(&timestamp_buffer[9],&end, 4);
  log(timestamp_buffer, 1+3*4);
}
