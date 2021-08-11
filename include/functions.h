#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

int bthci_event_AttemptToEnqueueEventToTransport(char* buffer);
char* bthci_event_AllocateEventAndFillHeader(uint8_t len_total, char event_code, uint8_t len_data);

void* memcpy(void *dst, void* src, uint32_t size);
void * memcpybt8(void* dst, void* src, uint32_t size);

uint32_t clock_SystemTimeMicroseconds32_nolock();
int lm_getRawRssiWithTaskId();

#endif
