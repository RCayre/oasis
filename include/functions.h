#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

int bthci_event_AttemptToEnqueueEventToTransport(char* buffer);
char* bthci_event_AllocateEventAndFillHeader(uint8_t len_total, char event_code, uint8_t len_data);

void* memcpy(void *dst, void* src, uint32_t size);
void * memcpybt8(void* dst, void* src, uint32_t size);

uint32_t clock_SystemTimeMicroseconds32_nolock();
int lm_getRawRssiWithTaskId();

// Both Sys or Nat work as a timestamp
void btclk_GetNatClk_clkpclk(uint64_t * t);
void btclk_GetSysClk_clkpclk(void * p, uint64_t * t);
uint32_t btclk_Convert_clkpclk_us(uint64_t * p);

#endif
