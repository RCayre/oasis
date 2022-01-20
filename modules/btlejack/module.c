#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "hashmap.h"
#include "malloc.h"
#include "alert.h"

#define BTLEJACK_ALERT_NUMBER 1
#define TYPE_TX_PACKET 0
#define TYPE_RX_PACKET 1

#define HASHMAP_SIZE 16
typedef struct btlejack_data {
  uint32_t invalid_counter;
  bool is_init;
} btlejack_data_t;

static hashmap_t * btlejack_hashmap = NULL;

void btlejack_detection(metrics_t * metrics, int type) {
  if(metrics->local_device->gap_role == CENTRAL) {
		if(btlejack_hashmap == NULL) {
			btlejack_hashmap = hashmap_initialize(HASHMAP_SIZE, NULL, 4);
		}

		// Get this device's data for detecting a BTLEJack attack
		btlejack_data_t * data;
		void * ret = hashmap_get(btlejack_hashmap, (uint8_t*)&metrics->current_connection->access_address);
		if(ret == NULL) {
			// Add an entry if it wasn't found
			data = (btlejack_data_t *) malloc(sizeof(btlejack_data_t));
			data->invalid_counter = 0;
			data->is_init = 0;
			int err = hashmap_put(btlejack_hashmap, (uint8_t*)&metrics->current_connection->access_address, data);
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

		if ((type == TYPE_RX_PACKET && !metrics->current_packet->valid) || metrics->current_connection->packets_lost_counter > 0) {
			data->invalid_counter++;
		}
		if(data->invalid_counter > 3) {
      alert(BTLEJACK_ALERT_NUMBER,(uint8_t*)&metrics->current_connection->access_address, 4);
		}

		if ((type == TYPE_RX_PACKET && metrics->current_packet->valid) && metrics->current_connection->packets_lost_counter == 0) {
			data->invalid_counter = 0;
		}
	}
}

void CONN_TX_CALLBACK(btlejack)(metrics_t * metrics) {
  btlejack_detection(metrics,TYPE_TX_PACKET);
}

void CONN_RX_CALLBACK(btlejack)(metrics_t * metrics) {
  btlejack_detection(metrics,TYPE_RX_PACKET);
}

void CONN_DELETE_CALLBACK(btlejack)(metrics_t * metrics) {
  hashmap_delete(btlejack_hashmap, (uint8_t*)&metrics->current_connection->access_address);
}
