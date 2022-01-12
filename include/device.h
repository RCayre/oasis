#ifndef DEVICE_H
#define DEVICE_H
#include "packet.h"
typedef enum gap_role {
  ADVERTISER = 0,
  PERIPHERAL = 1,
  SCANNER = 2,
  CENTRAL = 3
} gap_role_t;

typedef struct device {
  address_type_t address_type;
  gap_role_t gap_role;
  uint32_t advertisements_interval;
  uint32_t connection_interval;
  uint8_t address[6];
} device_t;

#endif
