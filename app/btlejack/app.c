#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "log.h"
#include "hashmap.h"
#include "malloc.h"

#define HASHMAP_SIZE 16

typedef struct btlejack_data {
  uint32_t invalid_counter;
  bool is_init;
} btlejack_data_t;

static hashmap_t * hashmap = NULL;

void btlejack_detection(metrics_t * metrics) {
	if (!is_slave()) {
		if(hashmap == NULL) {
			hashmap = hashmap_initialize(HASHMAP_SIZE, NULL, 4);
		}

		// Get this device's data for detecting a mitm attack
		btlejack_data_t * data;
		void * ret = hashmap_get(hashmap, metrics->conn_access_addr);
		if(ret == NULL) {
			// Add an entry if it wasn't found
			data = (btlejack_data_t *) malloc(sizeof(btlejack_data_t));
			data->invalid_counter = 0;
			data->is_init = 0;
			int err = hashmap_put(hashmap, metrics->conn_access_addr, data);
			// If there was not enough memory, skip
			if(err == -1) {
				return;
			}
		} else {
			data = (btlejack_data_t*)ret;
		}

		if(!data->is_init) {
			data->is_init = 1;
		}

		if (!metrics->conn_rx_crc_good || metrics->consecutive_missed_packets > 0) {
			data->invalid_counter++;
		}
		if(data->invalid_counter > 3) {
			log(NULL, "BTLEJACK", 8);
		}

		if(metrics->conn_rx_crc_good && metrics->consecutive_missed_packets == 0) {
			data->invalid_counter = 0;
		}
	}
}
void CONN_TX_CALLBACK(btlejack)(metrics_t * metrics) {
  btlejack_detection(metrics);
}

void CONN_RX_CALLBACK(btlejack)(metrics_t * metrics) {
  btlejack_detection(metrics);
}
