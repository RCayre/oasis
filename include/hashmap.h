#ifndef HASHMAP_H
#define HASHMAP_H

#include <types.h>

#include "functions.h"

/* This is an implementation of a hashmap where keys are advertising addresses
 * and values can be anything. This choice was made because of the time and
 * space constraints of the system.
 * Advertising addresses are store as an array of 6 bytes */

#define ADV_ADDR_SIZE 6

typedef struct hashmap_entry {
  uint8_t addr[6];
  void * data;
  struct hashmap_entry *next;
} hashmap_entry_t;

typedef struct hashmap {
  hashmap_entry_t ** buckets;
  uint32_t size;
} hashmap_t;

/**
 * @brief Creates a hashmap
 * @param size      number of buckets in the hashmap
 * @return the newly created hashmap
 */
hashmap_t * hashmap_initialize(uint32_t size);

/**
 * @brief Frees a hashmap
 * @param size      number of buckets in the hashmap
 * @return the newly created hashmap
 */
void hashmap_free(hashmap_t **hashmap);

/**
 * @brief Adds an entry to the hashmap
 * @param hashmap   the hashmap involved in the operation
 * @param addr      the data's key in the hashmap
 * @param data      a pointer to the data to be inserted
 * @param size      the size of the data
 */
int hashmap_put(hashmap_t *hashmap, uint8_t *addr, void *data, uint32_t size);

/**
 * @brief Deletes an entry from the hashmap
 * @param hashmap   the hashmap involved in the operation
 * @param addr      the entry's key in the hashmap
 */
void hashmap_delete(hashmap_t *hashmap, uint8_t * addr);

/**
 * @brief Retreives an entry from the hashmap
 * @param hashmap   the hashmap involved in the operation
 * @param addr      the entry's key in the hashmap
 * @return a pointer to the found entry
 *         This function returns a NULL pointer if no entry was found
 */
void *hashmap_get(hashmap_t *hashmap, uint8_t * addr);

#endif
