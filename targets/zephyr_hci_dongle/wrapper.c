
#include "wrapper.h"
#include "events.h"
#include "malloc.h"

/* Constants and peripherals registers */
// Gap roles constants
#define GAP_ROLE_ADVERTISER 0
#define GAP_ROLE_PERIPHERAL 1
#define GAP_ROLE_SCANNER    2
#define GAP_ROLE_CENTRAL    3

// Peripherals registers
#define TIMER2_MODE ((uint32_t*)0x4000A504)
#define TIMER2_WIDTH ((uint32_t*)0x4000A508)
#define TIMER2_PRESCALER ((uint32_t*)0x4000A510)
#define TIMER2_INTENSET ((uint32_t*)0x4000A304)
#define TIMER2_INTENCLR ((uint32_t*)0x4000A308)
#define TIMER2_CLEAR ((uint32_t*)0x4000A00c)
#define TIMER2_START ((uint32_t*)0x4000A000)
#define TIMER2_SHORTS ((uint32_t*)0x4000A200)

#define TIMER2_CAPTURE1 ((uint32_t*)0x4000A044)
#define TIMER2_CC1 ((uint32_t*)0x4000A544)

#define RADIO_PACKETPTR ((uint32_t*)0x40001504)
#define RADIO_FREQUENCY ((uint32_t*)0x40001508)

/* Controller functions used by the wrapper */
void * memcpy (void * dst, void * src, uint32_t size);
uint8_t radio_is_done ();
bool radio_crc_is_valid ();
uint8_t * ll_addr_get (uint8_t addr_type);
void * bt_hci_evt_create (uint8_t opcode, size_t size);
void * net_buf_simple_add (void * evt, size_t size);
void bt_recv (void *evt);

/* Global variables used internally by the wrapper */
extern uint32_t CODE_START[];
extern uint32_t DATA_START[];
extern uint32_t DATA_SIZE[];

uint8_t current_gap_role = 0;
uint32_t access_address = 0x00000000;
uint32_t crc_init = 0x00000000;
uint16_t hop_interval = 0x0000;
uint8_t channel_map[5];
bool connected = false;
uint32_t last_timestamp_in_event_loop = 0;

/* Generic Wrapper API */
// Utilities functions

void * memset(void * dst, uint8_t value, uint32_t size) {
	for (int i=0;i<size;i++) {
		*(uint8_t*)(dst+i) = value;
	}
}

// Time-related functions
void timer2_init() {
    *TIMER2_MODE = 0;
	*TIMER2_WIDTH = 3;
	*TIMER2_PRESCALER = 4;

    *TIMER2_INTENCLR = (0xfff << 16);

    *TIMER2_START = 1;
    *TIMER2_CLEAR = 1;
}

uint32_t get_timestamp_in_us() {
    *TIMER2_CAPTURE1 = 1;
    return *TIMER2_CC1;
}

uint32_t now() {
    return get_timestamp_in_us();
}

// Packet-related functions

bool is_crc_good() {
    return radio_crc_is_valid();
}

int get_rssi() {
    return 0;
}

void copy_header(uint8_t * dst) {
    memcpy(dst, (void*)*RADIO_PACKETPTR, 2);
}

bool is_rx_done() {
    return (radio_is_done() & 0xFF) != 0;
}

void copy_buffer(uint8_t * dst, uint8_t size) {
    memcpy(dst, (void*)(*RADIO_PACKETPTR + 2), size);
}

// Multi-role functions


void copy_own_bd_addr(uint8_t * dst) {
    uint8_t *address = ll_addr_get(0);
    memcpy(dst, address,6);
}

uint8_t get_channel() {
    uint8_t channel = 0;
    uint32_t frequency = *(uint32_t*)RADIO_FREQUENCY;
    if (frequency == 2) channel = 37;
    else if (frequency == 80) channel = 39;
    else if (frequency == 26) channel = 38;
    else if (frequency < 24) channel = (frequency/2) - 2;
    else channel = (frequency/2) - 3;
    return channel;
}

uint8_t get_current_gap_role() {
    return current_gap_role;
}

// Connection-related functions
#ifdef CONNECTION_ENABLED
bool is_slave() {
    return connected && current_gap_role == GAP_ROLE_PERIPHERAL;
}

void copy_channel_map(uint8_t * dst) {
    memcpy(dst,channel_map,5);
}

uint16_t get_hop_interval() {
    return hop_interval;
}

uint32_t get_crc_init() {
    return crc_init;
}

void copy_access_addr(uint32_t * dst) {
    memcpy(dst,&access_address,4);
}
#endif

/* Actions API */
void start_scan() {
    // TODO: not implemented
}

void stop_scan() {
    // TODO: not implemented
}

void send_hci_event(uint8_t opcode, void * content, uint32_t size) {
    void * evt = bt_hci_evt_create(opcode, size);
    uint8_t * buf = net_buf_simple_add(evt+8, size);
    memcpy(buf, content, size);
    bt_recv(evt);
}

void log(uint8_t* buffer,uint8_t size) {
    send_hci_event(0xFF, buffer, size);
}
/* Hooks */
// Initialisation hook
void on_init() {
    uint32_t RAM_ZONE_START = (uint32_t)CODE_START - (uint32_t)DATA_SIZE;
    memcpy((void*)DATA_START, (void*)RAM_ZONE_START,(uint32_t)DATA_SIZE);
    timer2_init();
}

// Time-related hook
void on_event_loop() {
	uint32_t current_time = now();
	if (current_time - last_timestamp_in_event_loop > 1000000) {
		last_timestamp_in_event_loop = current_time;
		process_time();
	}
}


#ifdef SCAN_ENABLED
// Scan Reception hook
void on_scan() {
    process_scan_rx_header();
    process_scan_rx();
}
#endif

#ifdef CONNECTION_ENABLED
// Central startup hook
void on_setup_central(void *rx, void *ftr, void *lll) {
    connected = true;
    current_gap_role = GAP_ROLE_CENTRAL;

    // Copy access address
    memcpy(&access_address, lll+4, 4);
    // Copy CRC Init
    memcpy(&crc_init, lll+8, 4);
    // Copy Hop Interval
    memcpy(&hop_interval, lll+14, 2);
    // Copy channel map
    memcpy(&channel_map, lll+24, 5);

    process_conn_init();
}

// Central cleanup hook
void on_cleanup_central() {
	if (connected != false) {
		process_conn_delete();
		connected = false;
	}
}
#endif


#ifdef CONNECTION_ENABLED
// Peripheral startup hook
void on_setup_peripheral(void *rx, void *ftr, void *lll) {
    connected = true;
    current_gap_role = GAP_ROLE_PERIPHERAL;

	// Copy access address
	memcpy(&access_address, lll+4, 4);
	// Copy CRC Init
	memcpy(&crc_init, lll+8, 4);
	// Copy Hop Interval
	memcpy(&hop_interval, lll+14, 2);
	// Copy channel map
	memcpy(&channel_map, lll+24, 5);

    process_conn_init();
}
#endif

#ifdef CONNECTION_ENABLED
// Connection Transmission hook
void on_conn_tx(uint32_t *cb) {
    process_conn_tx();
}

// Connection Reception hook
void on_conn_rx() {
    process_conn_rx_header();
    process_conn_rx(true);
}
#endif
