#ifndef CALLBACKS_H
#define CALLBACKS_H

#define SCAN_CALLBACK(name) \
  _scan_callback_## name

#define CONN_RX_CALLBACK(name) \
  _conn_rx_callback_## name

#define CONN_TX_CALLBACK(name) \
  _conn_tx_callback_## name

#endif
