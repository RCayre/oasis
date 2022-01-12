#ifndef EVENTS_H
#define EVENTS_H

#include "types.h"

void process_time();
#ifdef SCAN_ENABLED
void process_scan_rx_header();
void process_scan_rx();
void process_scan_delete();
#endif
#ifdef CONNECTION_ENABLED
void process_conn_init();
void process_conn_rx_header();
void process_conn_rx(bool adapt_timestamp);
void process_conn_tx();
void process_conn_delete();
#endif
#endif
