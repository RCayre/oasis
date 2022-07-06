#include "alert.h"

void alert(uint8_t number, uint8_t *data, size_t data_size) {
  uint8_t alert_buffer[data_size+2];
  alert_buffer[0] = MESSAGE_TYPE_ALERT;
  alert_buffer[1] = number;
  memcpy(&alert_buffer[2],data, data_size);
  log(alert_buffer, 2+data_size);
}
