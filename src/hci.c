#include "hci.h"

#include "functions.h"

void send_hci(uint8_t opcode, void *content, uint32_t size) {
	char *hci_buffer = bthci_event_AllocateEventAndFillHeader(size + 2, opcode, size);
	memcpy(hci_buffer + 10, content, size);
	bthci_event_AttemptToEnqueueEventToTransport(hci_buffer);
}
