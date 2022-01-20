#include "alert.h"
#include "wrapper.h"

void alert(uint8_t number, uint8_t *data, size_t data_size) {
  uint8_t alert_buffer[data_size+1];
  alert_buffer[0] = number;
  memcpy(&alert_buffer[1],data, data_size);
  log(alert_buffer, 1+data_size);
}
