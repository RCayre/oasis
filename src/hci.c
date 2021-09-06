#include "hci.h"

#include "functions.h"

void send_hci(uint8_t opcode, void *content, uint32_t size) {
#ifdef BOARD_BCM4335C0
  char *hci_buffer = bthci_event_AllocateEventAndFillHeaderOld(opcode, size + 2);
  memcpy(hci_buffer + 2, content, size);
  bthci_event_AttemptToEnqueueEventToTransportWithoutFree(hci_buffer); 
  bthci_event_FreeEvent(hci_buffer);
#else
	char *hci_buffer = bthci_event_AllocateEventAndFillHeader(size + 2, opcode, size);
	memcpy(hci_buffer + 10, content, size);
	bthci_event_AttemptToEnqueueEventToTransport(hci_buffer);
#endif
}
