#include "hashmap.h"

#include "hci.h"
#include "malloc.h"
#include "log.h"

#define NULL (void*)0

uint32_t hash(hashmap_t * hashmap, uint8_t * addr) {
  int h = 0;
  for(int i = 0; i < 6; i++) {
    h += addr[i];
  }
  return h % (hashmap->size - 1);
}

hashmap_t * hashmap_initialize(uint32_t size, bool (*check_to_remove)(void *)) {
  hashmap_t * hashmap = (hashmap_t *) malloc(sizeof(hashmap_t));
  hashmap->buckets = (hashmap_entry_t **) malloc(size * sizeof(hashmap_entry_t *));
  for(uint32_t i = 0; i < size; i++) {
    hashmap->buckets[i] = NULL;
  }
  hashmap->size = size;
  hashmap->check_to_remove = check_to_remove;
  return hashmap;
}

bool compare_addr(uint8_t * addr_a, uint8_t * addr_b) {
  bool is_equal = 1;
  uint8_t i = 0;
  while(is_equal && i < ADV_ADDR_SIZE) {
    is_equal = (addr_a[i] == addr_b[i]);
    i += 1;
  }

  return is_equal;
}

void hashmap_free(hashmap_t **hashmap) {
  for(uint32_t i = 0; i < (*hashmap)->size; i++) {
    hashmap_entry_t * entry = (*hashmap)->buckets[i];
    // free the whole linked list
    while(entry != NULL) {
      // save the next element
      hashmap_entry_t * next = entry->next;
      free(entry);
      entry = next;
    }
  }
  *hashmap = NULL;
}

void hashmap_declutter(hashmap_t *hashmap) {
  if(hashmap->check_to_remove != NULL) {
    for(int i = 0; i < hashmap->size; i++) {
      hashmap_entry_t * entry = hashmap->buckets[i];
      while(entry != NULL) {
        // Checks with the user provided function if the 
        // entry should be removed
        if(hashmap->check_to_remove(entry)) {
          hashmap_delete(hashmap, entry->addr);
        }
      }
    }
  }
}

int hashmap_put(hashmap_t *hashmap, uint8_t * addr, void *data) {
  // Removes unnecessary items from the hashmap if possible
  hashmap_declutter(hashmap);

  uint32_t key = hash(hashmap, addr);

  // Create the entry
  hashmap_entry_t * entry = (hashmap_entry_t *) malloc(sizeof(hashmap_entry_t));
  if(entry == NULL) {
    return -1;
  }
  // Addr
  memcpy(entry->addr, addr, 6);
  // Data
  entry->data = data;
  // Next
  entry->next = NULL;

  // Add the entry to the hashmap
  hashmap_entry_t * bucket = hashmap->buckets[key];
  if(bucket == NULL) {
    hashmap->buckets[key] = entry;
  } else {
    // If not empty, add to the top
    entry->next = hashmap->buckets[key];
    hashmap->buckets[key] = entry;
  }
  return 0;
}

void hashmap_delete(hashmap_t *hashmap, uint8_t * addr) {
  uint32_t key = hash(hashmap, addr);

  // Find the element before the entry to be deleted
  hashmap_entry_t * cur = hashmap->buckets[key];
  // Check if there is a bucket
  // Check if there is at least two elements
  // Check if the next one has the right address
  while(cur != NULL || 
      (cur->next == NULL && !compare_addr(cur->addr, addr)) || 
      (cur->next != NULL && !compare_addr(cur->next->addr, addr))) {
    cur = cur->next;
  }

  // Remove it
  if(cur != NULL) {
    // If there was a bucket with the right address
    if(cur->next == NULL) {
      // If it was alone
      hashmap->buckets[key] = NULL;
      free(cur);
    } else {
      // If there were at least two
      cur->next = cur->next->next;
      free(cur->next);
    }
  }
}

void *hashmap_get(hashmap_t *hashmap, uint8_t * addr) {
  uint32_t key = hash(hashmap, addr);

  // Find the entry
  hashmap_entry_t * cur = hashmap->buckets[key];
  uint8_t found = 0;
  while(!found && cur != NULL) {
    found = compare_addr(cur->addr, addr);
    if(!found) {
      cur = cur->next;
    }
  }

  if(cur == NULL) {
    return NULL;
  } else {
    return cur->data;
  }
}
