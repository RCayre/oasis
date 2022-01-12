#ifndef METRICS_H
#define METRICS_H

#include "types.h"
#include "packet.h"
#include "device.h"
#include "connection.h"

typedef struct metrics {
  packet_t *current_packet;
  device_t *current_device;
  connection_t *current_connection;
  device_t *local_device;
} metrics_t;

#endif
