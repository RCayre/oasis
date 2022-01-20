#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "hashmap.h"
#include "malloc.h"
#include "alert.h"

#define INJECTABLE_ALERT_NUMBER 3

#define WINDOW_SIZE 24
#define HASHMAP_SIZE 16
#define THRESHOLD 10

/* Sorted circular buffer definition */
typedef struct sorted_circular_buffer {
	uint32_t tab[WINDOW_SIZE];
	uint32_t indexes[WINDOW_SIZE];
	uint32_t pointer;
	bool full;
} sorted_circular_buffer_t;

typedef struct injectable_data {
  sorted_circular_buffer_t window;
  uint32_t last_hop_interval;
} injectable_data_t;

static hashmap_t * injectable_hashmap = NULL;

/* Insert a new value in the sorted circular buffer and removes the oldest one if the buffer is full */
void insert(sorted_circular_buffer_t* sa, int val) {
	int old_index = sa->indexes[sa->pointer];
	int size = (sa->full ? WINDOW_SIZE : sa->pointer);
	int i=0;
	while ((sa->full && i == old_index) || (i < size && sa->tab[i] <= val)) {
		i++;
	}
	if (sa->full && i == old_index+1) {
		sa->tab[i-1] = val;
		sa->indexes[sa->pointer] = i-1;
	}
	else {
		for (int j=0;j<size;j++) {
			int shift = 0;
			if (sa->indexes[j] >= i) shift++;
			if (sa->full && sa->indexes[j] >= old_index) shift--;

			sa->indexes[j] += shift;
		}

		int end = sa->full ? old_index : size;
		if (i < end) {
			for (int j=end-1;j>=i;j--) {
				sa->tab[j+1] = sa->tab[j];
			}
		}
		else {
			for (int j=end+1;j<=i;j++) {
				sa->tab[j-1] = sa->tab[j];
			}
		}
		if (i > end) i--;
		sa->tab[i] = val;
		sa->indexes[sa->pointer] = i;

	}
	sa->pointer = (sa->pointer + 1) % WINDOW_SIZE;
	if (sa->pointer == 0 && !sa->full) sa->full = true;
}

/* Returns the median of the sorted circular buffer (if it is full) */
uint32_t median(sorted_circular_buffer_t* sa) {
  return sa->tab[WINDOW_SIZE/6];
}

void CONN_DELETE_CALLBACK(injectable)(metrics_t *metrics) {
  hashmap_free(&injectable_hashmap);
}

void CONN_RX_CALLBACK(injectable)(metrics_t * metrics) {
  // This detection is intended to be used as a slave
  if(metrics->local_device->gap_role != PERIPHERAL) {
    return;
  }

  // If the hashmap doesn't exist, creates it
  if(injectable_hashmap == NULL) {
    injectable_hashmap = hashmap_initialize(HASHMAP_SIZE, NULL, 4);
  }

  // Get the connection data for detecting a injectable attack
  injectable_data_t * data;
  void * ret = hashmap_get(injectable_hashmap, (uint8_t*)&metrics->current_connection->access_address);


  if(ret == NULL) {
    // Add an entry if it wasn't found
    data = (injectable_data_t *) malloc(sizeof(injectable_data_t));
    for (int i=0;i<WINDOW_SIZE;i++) {
      data->window.tab[i] = 0;
      data->window.indexes[i] = 0;
    }
    data->window.pointer = 0;
    data->window.full = false;
    int err = hashmap_put(injectable_hashmap, (uint8_t*)&metrics->current_connection->access_address, data);

    // If there was not enough memory, skip
    if(err == -1) {
      return;
    }
  }
  // If an entry exists, get it
  else {
    data = (injectable_data_t*)ret;
  }

  // Exclude first value or invalid packet
  if(metrics->remote_device->connection_interval == 0 || !metrics->current_packet->valid) {
    return;
  }

  // If a new interval is used, resets the circular buffer
	if (data->last_hop_interval != metrics->remote_device->connection_interval) {
		data->window.full = false;
		data->window.pointer = 0;
	}
	data->last_hop_interval = metrics->remote_device->connection_interval;

  // If the sorted circular buffer is full, performs the detection
  if (data->window.full) {
    // get the current interval
    uint32_t current_interval = metrics->remote_device->connection_interval;
    // get the median of previous intervals
    uint32_t med = median(&data->window);

    int32_t error = (((current_interval - med/2) % med) - med/2);
		uint32_t absolute_error = (error >= 0 ? error : -error);
		absolute_error = (2000*absolute_error) / med;


    if (absolute_error <= THRESHOLD && absolute_error > 0) {
      // Raise an alert
      alert(INJECTABLE_ALERT_NUMBER,(uint8_t*)&metrics->current_connection->access_address, 4);
    }
  }

  // Insert the current interval in the sorted circular buffer
  insert(&data->window, metrics->remote_device->connection_interval);
}
