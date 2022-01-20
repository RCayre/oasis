#include "events.h"
#include "wrapper.h"
#include "metrics.h"
#include "malloc.h"
#include "hashmap.h"

#ifdef CONNECTION_ENABLED
#define TIMESTAMP_HASHMAP_SIZE 4

extern metrics_t metrics;

extern uint8_t conn_init_callbacks_size;
extern uint8_t conn_rx_callbacks_size;
extern uint8_t conn_tx_callbacks_size;
extern uint8_t conn_delete_callbacks_size;

extern callback_t conn_init_callbacks[];
extern callback_t conn_rx_callbacks[];
extern callback_t conn_tx_callbacks[];
extern callback_t conn_delete_callbacks[];

static hashmap_t * conn_timestamp_hashmap = NULL;

void process_conn_init() {

	connection_t* current_connection = metrics.current_connection;

	copy_channel_map(current_connection->channel_map);
	current_connection->hop_interval = get_hop_interval();
	copy_access_addr(&current_connection->access_address);
	current_connection->crc_init = get_crc_init();
	current_connection->tx_counter = 0;
	current_connection->rx_counter = 0;
	current_connection->packets_lost_counter = 0;

	for(int i = 0; i < conn_init_callbacks_size; i++) {
    conn_init_callbacks[i](&metrics);
  }
}


void process_conn_tx() {
	connection_t* current_connection = metrics.current_connection;

	current_connection->tx_counter++;
	packet_t* current_packet = metrics.current_packet;

	current_packet->channel = get_channel();
	current_packet->timestamp =  get_timestamp_in_us();

	for(int i = 0; i < conn_tx_callbacks_size; i++) {
    conn_tx_callbacks[i](&metrics);
  }

	current_connection->packets_lost_counter++;

}

void process_conn_rx_header() {
	packet_t* current_packet = metrics.current_packet;
	current_packet->timestamp = get_timestamp_in_us();
	copy_header(current_packet->header);
}

void process_conn_rx(bool adapt_timestamp) {

	connection_t* current_connection = metrics.current_connection;
	current_connection->packets_lost_counter = 0;
	copy_channel_map(current_connection->channel_map);
	copy_access_addr(&current_connection->access_address);
	current_connection->crc_init = get_crc_init();
	current_connection->hop_interval = get_hop_interval();
	current_connection->rx_counter += 1;

	local_device_t* local_device = metrics.local_device;
	copy_own_bd_addr(local_device->address);
	local_device->gap_role = (gap_role_t)get_current_gap_role();

	remote_device_t* remote_device = metrics.remote_device;
	remote_device->gap_role = (local_device->gap_role == PERIPHERAL ? CENTRAL : PERIPHERAL);

	packet_t* current_packet = metrics.current_packet;
  current_packet->rssi = get_rssi();
	if (adapt_timestamp) {
		current_packet->timestamp = current_packet->timestamp - (get_packet_size()+4+2+3)*8;
	}
	current_packet->channel = get_channel();
	current_packet->valid = is_crc_good();
	if (current_packet->valid) {
		copy_buffer(current_packet->content,get_packet_size());
	}

	if(conn_timestamp_hashmap == NULL) {
    conn_timestamp_hashmap = hashmap_initialize(TIMESTAMP_HASHMAP_SIZE, NULL, 4);
  }

	uint32_t* previous_timestamp = (uint32_t*)hashmap_get(conn_timestamp_hashmap, (uint8_t*)&current_connection->access_address);
	if(previous_timestamp == NULL) {
		uint32_t * current_timestamp_ptr = (uint32_t *) malloc(sizeof(uint32_t));
		*current_timestamp_ptr = current_packet->timestamp;
		hashmap_put(conn_timestamp_hashmap, (uint8_t*)&current_connection->access_address, current_timestamp_ptr);
		remote_device->connection_interval = 0;
	}
	else {
		if(current_packet->timestamp == *previous_timestamp) {
			remote_device->connection_interval = 0;
		}
		else {
			remote_device->connection_interval = current_packet->timestamp - *(uint32_t *)previous_timestamp;
			*(uint32_t *)previous_timestamp = current_packet->timestamp;
		}
	}

	for(int i = 0; i < conn_rx_callbacks_size; i++) {
    conn_rx_callbacks[i](&metrics);
  }
}

void process_conn_delete() {
	for(int i = 0; i < conn_delete_callbacks_size; i++) {
		conn_delete_callbacks[i](&metrics);
	}
	hashmap_delete(conn_timestamp_hashmap, (uint8_t*)&metrics.current_connection->access_address);
}

#endif
