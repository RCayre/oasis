#include "types.h"
#include "metrics.h"
#include "callbacks.h"
#include "hashmap.h"
#include "malloc.h"

#define WINDOW_SIZE 24
#define HASHMAP_SIZE 16
#define THRESHOLD 100

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

static hashmap_t * hashmap = NULL;
uint32_t injectable_detected = 0;


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

uint32_t median(sorted_circular_buffer_t* sa) {
  return sa->tab[WINDOW_SIZE/6];
}

uint32_t val[120];
uint32_t valp = 0;
uint32_t value = 0xFFFFFFFF;
uint32_t vvv = 0;
uint16_t update = 0;

void CONN_DELETE_CALLBACK(injectable)(metrics_t *metrics) {
  hashmap_free(&hashmap);
  hashmap = NULL;
}
void CONN_RX_CALLBACK(injectable)(metrics_t * metrics) {
  // This detection is intended to be used as a slave
  if(metrics->local_device->gap_role != PERIPHERAL) {
    return;
  }
  if(hashmap == NULL) {
    hashmap = hashmap_initialize(HASHMAP_SIZE, NULL, 4);
  }
  // Get this device's data for detecting a mitm attack
  injectable_data_t * data;
  void * ret = hashmap_get(hashmap, (uint8_t*)&metrics->current_connection->access_address);
  if(ret == NULL) {
    // Add an entry if it wasn't found
    data = (injectable_data_t *) malloc(sizeof(injectable_data_t));
    for (int i=0;i<WINDOW_SIZE;i++) {
      data->window.tab[i] = 0;
      data->window.indexes[i] = 0;
    }
    data->window.pointer = 0;
    data->window.full = false;
    int err = hashmap_put(hashmap, (uint8_t*)&metrics->current_connection->access_address, data);
    // If there was not enough memory, skip
    if(err == -1) {
      return;
    }
  } else {
    data = (injectable_data_t*)ret;
  }
  // Exclude first value
  if(metrics->remote_device->connection_interval == 0 || !metrics->current_packet->valid) {
    return;
  }

	if (data->last_hop_interval != (*((uint32_t*) (0x200007bc))>>16)) {
		data->window.full = false;
		data->window.pointer = 0;
	}
	data->last_hop_interval = (*((uint32_t*) (0x200007bc))>>16);
  int ok = 0;
  if (data->window.full) {
    uint32_t v = metrics->remote_device->connection_interval;

    uint32_t med = median(&data->window);
    int32_t tmp = (((v - med/2) % med) - med/2);
		uint32_t updated = (tmp >= 0 ? tmp : -tmp);
		updated = (2000*updated) / med;
    //val[valp] = (updated <= 10 && updated > 0 ? updated : 0);//updated > 0x10 && updated < 0x50;// > 1 ? *((uint32_t*) (0x200007bc))  : value;/*tmp > 20  && value != 0xAAAAAAAA ? metrics->current_packet->header[1] : value;*/
    //valp = (valp + 1) % 120;
    if (updated <= 10 && updated > 0) {
      log(&updated,4);
    }
  }
  else {
    ok = 1;
  }

   insert(&data->window, metrics->remote_device->connection_interval);

}
