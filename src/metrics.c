#include "metrics.h"

extern packet_t current_packet;
extern remote_device_t remote_device;
extern local_device_t local_device;
extern connection_t current_connection;

metrics_t metrics = {
  .current_packet = &current_packet,
  .remote_device = &remote_device,
  .current_connection  = &current_connection,
  .local_device = &local_device
};
