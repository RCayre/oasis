#include "malloc.h"
#include "wrapper.h"


typedef struct block {
  uint16_t size;
  uint8_t free;
  uint8_t pad;
  struct block * next;
} block_t;

// Memory region to be used for allocating data
__attribute__((section(".bss.memory")))
uint8_t memory[HEAP_SIZE];

// A linked list of the blocks in memory
block_t * blocks = NULL;

/**
 * @brief Splits a block in two block, one with a specific size and the other
 * with the rest
 * @param b     a pointer to the block being split
 * @param size  the size of the first block
 */

void split(block_t * b, uint16_t size) {
  // There needs to be enough room for the block metadata to perform a split
  if(b->size > size + sizeof(block_t)) {
    // Get the new block
  block_t * new = (block_t *)((uint8_t *)(b+1)+size);
    // Compute the new block size
    new->size = b->size - size - sizeof(block_t);

    new->free = 1;
    // Set the pointers for the list
    block_t * buf = b->next;
    new->next = buf;
    b->next = new;

    b->size = size;

  }
}

/**
 * @brief Check if two blocks can be merged. Merges them if it can
 * @param b     a pointer to the first block to be merged
 * @param size  the size goal for the merged block
 * @return true if the blocks where successfully merged
 */
uint8_t merge_if_possible(block_t * b, uint16_t size) {
  block_t * cur = b;
  uint32_t total_size = 0;
  // While there is a next block and the total size is lower than size
  while(cur != NULL && cur->next != NULL && total_size < size) {
    total_size += cur->size;
    if(total_size < size) {
      cur = cur->next;
    }
  }

  if(total_size >= size) {
    // If the found block accomodate the required size
    // skip the blocks in between
    b->next = cur;
    b->size = total_size;
    return 1;
  } else {
    return 0;
  }
}
int weird = 0;

void * malloc(uint16_t size) {
  #ifdef ALIGNED_MALLOC
  while ((size % 4) != 0) size++;
  #endif
  // Initialize the memory if new
  if(blocks == NULL) {
    blocks = (block_t*)memory;
    blocks->size = HEAP_SIZE - sizeof(block_t);
    blocks->free = 1;
    blocks->next = NULL;
  }

  // Loop through the blocks
  void * ret = 0;
  block_t * b = blocks;
  uint8_t found = 0;
  while(!found && b != NULL) {
    // Check if block is free
    if(b->free) {
      if(b->size == size) {
        // If exact same size
        b->free = 0;

        ret = (void*)(b + 1);
        found = 1;

      } else if(b->size > size) {

        // If too big, split the block if we can
        split(b, size);
        // Set block as not free
        b->free = 0;
        ret = (void*)(b + 1);
        found = 1;
      } else {

        // If too small, check if can be merged
        int is_merged = merge_if_possible(b, size);
        if(is_merged) {
          // Blocks were merged to accomodate the size
          if(b->size > size) {
            // Split the block if too big
            split(b, size);
          }
          b->free = 0;

          ret = (void*)(b + 1);
          found = 1;
        } else {
          // If didn't merge, go to next block
          b = b->next;
        }
      }
    } else {
      // If not free, go to next block
      b = b->next;
    }
  }
  if (((uint32_t)ret % 4) != 0) weird = 1;
  return ret;
}

void free(void * p) {
  // Loop through the blocks to find the pointer

  uint8_t found = 0;
  block_t * b = blocks;
  while(!found && b != NULL) {
    found = p == (void*)(b+1);
    if(!found) {
      b = b->next;
    }
  }

  if(found) {
    b->free = 1;
  }
}
