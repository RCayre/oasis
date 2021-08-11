#ifndef CALLBACKS_H
#define CALLBACKS_H

#define SCAN_CALLBACK(name) \
  _scan_callback_## name

#define CONN_CALLBACK(name) \
  _conn_callback_## name

#endif
