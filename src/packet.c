#include "packet.h"

packet_t current_packet;


uint8_t get_packet_size() {
  return current_packet.header[1];
}

#ifdef SCAN_ENABLED
adv_type_t get_adv_packet_type() {
  return (adv_type_t)(current_packet.header[0] & 0x0F);
}

adv_ind_t* get_adv_ind_dissector() {
  return (adv_ind_t*)current_packet.content;
}

address_type_t get_tx_address_type() {
  return (address_type_t)((current_packet.header[0] & 0x40) >> 6);
}
address_type_t get_rx_address_type() {
  return (address_type_t)((current_packet.header[0] & 0x80) >> 7);
}
#endif

#ifdef CONNECTION_ENABLED
uint8_t get_llid() {
  return current_packet.header[0] & 0x03;
}
#endif
