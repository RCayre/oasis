#ifndef PALLOC_H
#define PALLOC_H

#include "types.h"

typedef struct block {
  uint16_t size;
  uint8_t free;
  #ifdef ALIGNED_MALLOC
    uint8_t pad;
  #endif
  struct block * next;
} block_t;

/**
 * @brief Allocates memory
 * @param size  size in bytes
 * @return a pointer to the allocated memory
 */
void * malloc(uint16_t size);

/**
 * @brief Frees a pointer allocated with malloc
 * @param p   a pointer to the allocated memory
 */
void free(void * p);

#endif
