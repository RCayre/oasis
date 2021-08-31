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
  return h % (hashmap->nb_buckets - 1);
}

hashmap_t * hashmap_initialize(uint32_t nb_buckets, bool (*check_to_remove)(void *)) {
  hashmap_t * hashmap = (hashmap_t *) malloc(sizeof(hashmap_t));
  hashmap->buckets = (hashmap_entry_t **) malloc(nb_buckets * sizeof(hashmap_entry_t *));
  for(uint32_t i = 0; i < nb_buckets; i++) {
    hashmap->buckets[i] = NULL;
  }
  hashmap->nb_buckets = nb_buckets;
  hashmap->check_to_remove = check_to_remove;
  hashmap->nb_elements = 0;
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
  for(uint32_t i = 0; i < (*hashmap)->nb_buckets; i++) {
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
    for(int i = 0; i < hashmap->nb_buckets; i++) {
      hashmap_entry_t * entry = hashmap->buckets[i];
      while(entry != NULL) {
        // Checks with the user provided function if the 
        // entry should be removed
        if(hashmap->check_to_remove(entry->data)) {
          // Save the addr for deletion purposes
          uint8_t * addr = entry->addr;
          // Switch to the next before deleting
          entry = entry->next;
          hashmap_delete(hashmap, addr);
        } else {
          entry = entry->next;
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

  hashmap->nb_elements += 1;

  return 0;
}

void hashmap_delete(hashmap_t *hashmap, uint8_t * addr) {
  uint32_t key = hash(hashmap, addr);

  hashmap_entry_t * cur = hashmap->buckets[key];
  if(cur != NULL) {
    if(cur->next == NULL) {
      // Only one element
      if(compare_addr(cur->addr, addr)) {
        // Remove the element
        hashmap->buckets[key] = NULL;
        free(cur);
        hashmap->nb_elements -= 1;
      }
    } else {
      // More than one element
      // Find the element before the entry to be deleted
      bool found = 0;
      while(!found && cur->next != NULL) {
        found = compare_addr(cur->next->addr, addr);
        if(!found) {
          cur = cur->next;
        }
      }

      if(found) {
        // Remove the element after cur
        hashmap_entry_t * to_be_freed = cur->next;
        cur->next = cur->next->next;
        free(to_be_freed);
        hashmap->nb_elements -= 1;
      }
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
