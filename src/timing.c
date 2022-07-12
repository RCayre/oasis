#include "timing.h"

#ifdef TIMING_MEASUREMENT
timing_measures_t timing_measures;

void report_timestamps(event_type_t type) {
  bool send = false;
  uint32_t start = 0xFFFFFFFF;
  uint32_t end = 0xFFFFFFFF;
  uint32_t callbacks = 0xFFFFFFFF;
  uint32_t delay_modules = 0xFFFFFFFF;
  uint32_t delay_event = 0xFFFFFFFF;
  if (type == SCAN_EVENT) {
    start = timing_measures.scan_timestamp_start;
    end = timing_measures.scan_timestamp_end;
    callbacks = timing_measures.scan_timestamp_callbacks;
    delay_modules = end - callbacks;
    delay_event = end - start;
    if (timing_measures.scan_count < TIMING_AVERAGE_NUMBER) {
      timing_measures.scan_count++;
      timing_measures.scan_delay_event += delay_event;
      timing_measures.scan_delay_modules += delay_modules;
    }
    else {
      delay_event = (uint32_t)(timing_measures.scan_delay_event / timing_measures.scan_count);
      delay_modules = (uint32_t)(timing_measures.scan_delay_modules / timing_measures.scan_count);
      timing_measures.scan_count = 0;
      timing_measures.scan_delay_event = 0;
      timing_measures.scan_delay_modules = 0;
      send  = true;
    }
  }
  else if (type == CONN_INIT_EVENT) {
    start = timing_measures.conn_init_timestamp_start;
    end = timing_measures.conn_init_timestamp_end;
    callbacks = timing_measures.conn_init_timestamp_callbacks;
    delay_modules = end - callbacks;
    delay_event = end - start;
    if (timing_measures.conn_init_count < TIMING_AVERAGE_NUMBER) {
      timing_measures.conn_init_count++;
      timing_measures.conn_init_delay_event += delay_event;
      timing_measures.conn_init_delay_modules += delay_modules;
    }
    else {
      delay_event = (uint32_t)(timing_measures.conn_init_delay_event / timing_measures.conn_init_count);
      delay_modules = (uint32_t)(timing_measures.conn_init_delay_modules / timing_measures.conn_init_count);
      timing_measures.conn_init_count = 0;
      timing_measures.conn_init_delay_event = 0;
      timing_measures.conn_init_delay_modules = 0;
      send  = true;
    }

  }
  else if (type == CONN_DELETE_EVENT) {
    start = timing_measures.conn_delete_timestamp_start;
    end = timing_measures.conn_delete_timestamp_end;
    callbacks = timing_measures.conn_delete_timestamp_callbacks;

    delay_modules = end - callbacks;
    delay_event = end - start;
    if (timing_measures.conn_delete_count < TIMING_AVERAGE_NUMBER) {
      timing_measures.conn_delete_count++;
      timing_measures.conn_delete_delay_event += delay_event;
      timing_measures.conn_delete_delay_modules += delay_modules;
    }
    else {
      delay_event = (uint32_t)(timing_measures.conn_delete_delay_event / timing_measures.conn_delete_count);
      delay_modules = (uint32_t)(timing_measures.conn_delete_delay_modules / timing_measures.conn_delete_count);
      timing_measures.conn_delete_count = 0;
      timing_measures.conn_delete_delay_event = 0;
      timing_measures.conn_delete_delay_modules = 0;
      send  = true;
    }

  }
  else if (type == CONN_RX_EVENT) {
    start = timing_measures.conn_rx_timestamp_start;
    end = timing_measures.conn_rx_timestamp_end;
    callbacks = timing_measures.conn_rx_timestamp_callbacks;

    delay_modules = end - callbacks;
    delay_event = end - start;
    if (timing_measures.conn_rx_count < TIMING_AVERAGE_NUMBER) {
      timing_measures.conn_rx_count++;
      timing_measures.conn_rx_delay_event += delay_event;
      timing_measures.conn_rx_delay_modules += delay_modules;
    }
    else {
      delay_event = (uint32_t)(timing_measures.conn_rx_delay_event / timing_measures.conn_rx_count);
      delay_modules = (uint32_t)(timing_measures.conn_rx_delay_modules / timing_measures.conn_rx_count);
      timing_measures.conn_rx_count = 0;
      timing_measures.conn_rx_delay_event = 0;
      timing_measures.conn_rx_delay_modules = 0;
      send  = true;
    }

  }
  else if (type == CONN_TX_EVENT) {
    start = timing_measures.conn_tx_timestamp_start;
    end = timing_measures.conn_tx_timestamp_end;
    callbacks = timing_measures.conn_tx_timestamp_callbacks;

    delay_modules = end - callbacks;
    delay_event = end - start;
    if (timing_measures.conn_tx_count < TIMING_AVERAGE_NUMBER) {
      timing_measures.conn_tx_count++;
      timing_measures.conn_tx_delay_event += delay_event;
      timing_measures.conn_tx_delay_modules += delay_modules;
    }
    else {
      delay_event = (uint32_t)(timing_measures.conn_tx_delay_event / timing_measures.conn_tx_count);
      delay_modules = (uint32_t)(timing_measures.conn_tx_delay_modules / timing_measures.conn_tx_count);
      timing_measures.conn_tx_count = 0;
      timing_measures.conn_tx_delay_event = 0;
      timing_measures.conn_tx_delay_modules = 0;
      send  = true;
    }

  }
  else if (type == TIME_EVENT) {
    start = timing_measures.time_timestamp_start;
    end = timing_measures.time_timestamp_end;
    callbacks = timing_measures.time_timestamp_callbacks;


    delay_modules = end - callbacks;
    delay_event = end - start;
    if (timing_measures.time_count < TIMING_AVERAGE_NUMBER) {
      timing_measures.time_count++;
      timing_measures.time_delay_event += delay_event;
      timing_measures.time_delay_modules += delay_modules;
    }
    else {
      delay_event = (uint32_t)(timing_measures.time_delay_event / timing_measures.time_count);
      delay_modules = (uint32_t)(timing_measures.time_delay_modules / timing_measures.time_count);
      timing_measures.time_count = 0;
      timing_measures.time_delay_event = 0;
      timing_measures.time_delay_modules = 0;
      send  = true;
    }

  }
  if (send) {
    uint8_t timestamp_buffer[2+2*4];
    timestamp_buffer[0] = MESSAGE_TYPE_TIMING;
    timestamp_buffer[1] = type;
    memcpy(&timestamp_buffer[2],&delay_event, 4);
    memcpy(&timestamp_buffer[6],&delay_modules, 4);
    log(timestamp_buffer, 2+2*4);
  }
}
#endif
