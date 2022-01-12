#ifndef HASHMAP_H
#define HASHMAP_H

#include <types.h>
#include "wrapper.h"

/* This is an implementation of a hashmap where keys are advertising addresses
 * and values can be anything. This choice was made because of the time and
 * space constraints of the system.
 * Advertising addresses are store as an array of 6 bytes */

#define ADV_ADDR_SIZE 6

typedef struct hashmap_entry {
  uint8_t * addr;
  void * data;
  struct hashmap_entry *next;
} hashmap_entry_t;

typedef struct hashmap {
  hashmap_entry_t ** buckets;
  uint32_t nb_buckets;
  bool (*check_to_remove)(void *);
  uint32_t nb_elements;
  uint8_t addr_size;
} hashmap_t;

/**
 * @brief Creates a hashmap
 * @param nb_buckets      number of buckets in the hashmap
 * @param check_to_remove   a function that checks if an item should be removed
 * @return the newly created hashmap
 */
hashmap_t * hashmap_initialize(uint32_t nb_buckets, bool (*check_to_remove)(void *), uint8_t addr_size);

/**
 * @brief Frees a hashmap
 * @param nb_buckets      number of buckets in the hashmap
 * @return the newly created hashmap
 */
void hashmap_free(hashmap_t **hashmap);

/**
 * @brief Adds an entry to the hashmap
 * @param hashmap   the hashmap involved in the operation
 * @param addr      the data's key in the hashmap
 * @param data      a pointer to the data to be inserted
 *    This function takes ownership of data
 */
int hashmap_put(hashmap_t *hashmap, uint8_t *addr, void *data);

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
