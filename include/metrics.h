#ifndef METRICS_H
#define METRICS_H

#include "types.h"
#include "packet.h"
#include "device.h"
#include "connection.h"

typedef struct metrics {
  packet_t *current_packet;
  connection_t *current_connection;
  local_device_t *local_device;
  remote_device_t *remote_device;
} metrics_t;

#endif
