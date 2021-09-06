#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

int bthci_event_AttemptToEnqueueEventToTransport(char* buffer);
int bthci_event_AttemptToEnqueueEventToTransportWithoutFree(char* buffer);
char* bthci_event_AllocateEventAndFillHeader(uint8_t len_total, char event_code, uint8_t len_data);
char* bthci_event_AllocateEventAndFillHeaderOld(uint8_t len_total, char event_code);
void bthci_event_FreeEvent(char * event);

void * memcpy(void *dst, void* src, uint32_t size);
void * memcpybt8(void* dst, void* src, uint32_t size);

int lm_getRawRssiWithTaskId();

void btclk_GetNatClk_clkpclk(uint32_t * t);
uint32_t btclk_Convert_clkpclk_us(uint32_t * p);

#endif
