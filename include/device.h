#ifndef DEVICE_H
#define DEVICE_H
#include "packet.h"
typedef enum gap_role {
  ADVERTISER = 0,
  PERIPHERAL = 1,
  SCANNER = 2,
  CENTRAL = 3
} gap_role_t;

typedef struct local_device {
  gap_role_t gap_role;
  uint8_t address[6];
} local_device_t;

typedef struct remote_device {
  address_type_t address_type;
  gap_role_t gap_role;
  uint8_t address[6];
  #ifdef SCAN_ENABLED
  uint32_t advertisements_interval;
  #endif
  #ifdef CONNECTION_ENABLED
  uint32_t connection_interval;
  #endif
} remote_device_t;
#endif
