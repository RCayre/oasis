#ifndef CALLBACKS_H
#define CALLBACKS_H

#define SCAN_CALLBACK(name) \
  _scan_callback_## name

#define TIME_CALLBACK(name) \
  _time_callback_## name

#define CONN_RX_CALLBACK(name) \
  _conn_rx_callback_## name

#define CONN_TX_CALLBACK(name) \
  _conn_tx_callback_## name

#define CONN_INIT_CALLBACK(name) \
  _conn_init_callback_## name

#define CONN_DELETE_CALLBACK(name) \
  _conn_delete_callback_## name
  
#endif
