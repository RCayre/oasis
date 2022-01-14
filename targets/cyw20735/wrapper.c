
#include "wrapper.h"
#include "events.h"
#include "malloc.h"

/* Offsets used in connection structure */
#define GAP_ROLE_ADVERTISER 0
#define GAP_ROLE_PERIPHERAL 1
#define GAP_ROLE_SCANNER    2
#define GAP_ROLE_CENTRAL    3

#ifdef CONNECTION_ENABLED

uint8_t IS_SLAVE_OFFSET = 15;
uint8_t CHANNEL_OFFSET = 131;
uint8_t SECOND_STRUCT_OFFSET = 80;
uint8_t HOP_INTERVAL_OFFSET_IN_SECOND_STRUCT = 6;
uint8_t CHANNEL_MAP_OFFSET_IN_SECOND_STRUCT = 12;
uint8_t CRC_INIT_OFFSET_IN_SECOND_STRUCT = 0;
uint8_t ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT = 52;

#endif
/* Controller functions used by the wrapper */
void * __rt_memcpy (void * dst, void * src, uint32_t size);
void * utils_memcpy8 (void * dst, void * src, uint32_t size);
void btclk_GetNatClk_clkpclk (uint32_t * t);
uint32_t btclk_Convert_clkpclk_us (uint32_t *p);
int lm_getRawRssiWithTaskId ();
char * bthci_event_AllocateEventAndFillHeader (uint8_t len_total, char event_code, uint8_t len_data);
void bthci_event_AttemptToEnqueueEventToTransport (char *event);
/* Hardware registers and variables used by the wrapper */
uint8_t * rx_header_register = (uint8_t *) 0x318b98;
uint8_t * rx_register = (uint8_t *) 0x370c00;
uint8_t * status_register = (uint8_t *) 0x318bac;
uint8_t * channel = (uint8_t *) 0x283356;
uint8_t * hci_callbacks_table = (uint8_t *) 0x143eac;
uint8_t * bd_address = (uint8_t *) 0x280ca4;
/* Global variables used internally by the wrapper */
uint8_t current_gap_role;
void *connection_structure;
uint32_t last_timestamp_in_event_loop;
uint8_t connected = 0;

/* Generic Wrapper API */
// Utilities functions

void * memcpy(void * dst, void * src, uint32_t size) {
    return __rt_memcpy(dst, src, size);
}


// Time-related functions

uint32_t get_timestamp_in_us() {
    uint32_t t[2];
    btclk_GetNatClk_clkpclk(t);
    return btclk_Convert_clkpclk_us(t);
}

uint32_t now() {
    return get_timestamp_in_us();
}

// Packet-related functions

int get_rssi() {
    return lm_getRawRssiWithTaskId();
}

void copy_header(uint8_t * dst) {
    utils_memcpy8(dst, rx_header_register, 2);
}

bool is_rx_done() {
    return *status_register & 0x4;
}

void copy_buffer(uint8_t * dst, uint8_t size) {
    utils_memcpy8(dst, rx_register, size);
}

bool is_crc_good() {
    return (*status_register & 0x2) == 2;
}

// Multi-roles functions

uint8_t get_current_gap_role() {
    return current_gap_role;
}

void copy_own_bd_addr(uint8_t * dst) {
    memcpy(dst, bd_address, 6);
}


uint8_t get_channel() {
    #ifdef SCAN_ENABLED
    if (current_gap_role == GAP_ROLE_ADVERTISER || current_gap_role == GAP_ROLE_SCANNER) {
        return 37+*channel;
    }
    #endif
    #ifdef CONNECTION_ENABLED
    if (current_gap_role == GAP_ROLE_CENTRAL || current_gap_role == GAP_ROLE_PERIPHERAL) {
        return *(uint8_t *)(connection_structure + CHANNEL_OFFSET);
    }
    #endif
}

uint8_t get_current_channel() {
  return get_channel();
}
// Connection-related functions

#ifdef CONNECTION_ENABLED
bool is_slave() {
    return *(uint8_t *)(connection_structure + IS_SLAVE_OFFSET) != 0;
}

void copy_channel_map(uint8_t * dst) {
    void * p = *(void**)(connection_structure + SECOND_STRUCT_OFFSET);
    memcpy(dst, p + CHANNEL_MAP_OFFSET_IN_SECOND_STRUCT, 5);
}

uint16_t get_hop_interval() {
    void * p = *(void**)(connection_structure + SECOND_STRUCT_OFFSET);
    return *(uint16_t*)(p + HOP_INTERVAL_OFFSET_IN_SECOND_STRUCT);
}

uint32_t get_crc_init() {
    void * p = *(void**)(connection_structure + SECOND_STRUCT_OFFSET);
    return *(uint32_t*)(p + CRC_INIT_OFFSET_IN_SECOND_STRUCT);
}

void copy_access_addr(uint32_t * dst) {
    void * p = *(void**)(connection_structure + SECOND_STRUCT_OFFSET);
    memcpy(dst, p + ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT, 4);
}
#endif
/* Host-Controller Interface API */
void send_hci_event(uint8_t opcode, void * content, uint32_t size) {
    char *hci_buffer = bthci_event_AllocateEventAndFillHeader(size + 2, opcode, size);
    memcpy(hci_buffer + 10, content, size);
    bthci_event_AttemptToEnqueueEventToTransport(hci_buffer);
}

void run_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size) {
    uint8_t * param = (uint8_t *) malloc(size + 11);
    // Set first 11 bytes to 0
    for(uint8_t i = 0; i < 12; i++) {
    param[i] = 0;
    }
    // Copy the hci command parameter
    memcpy(param + 12, buffer, size);

    void (*handler)(uint8_t * buffer) = (void*)*(uint32_t *)(hci_callbacks_table + (opcode << 3) - 8);
    handler(param);
    free(param);
}
/* Actions API */
void start_scan() {
    uint8_t buffer[2];
    buffer[0] = 1;
    buffer[1] = 0;
    run_hci_command(0xc, buffer, 2);
}

void stop_scan() {
    uint8_t buffer[2];
    buffer[0] = 1;
    buffer[1] = 0;
    run_hci_command(0xc, buffer, 2);
}

void log(uint8_t *buffer, uint8_t size) {
    send_hci_event(0xFF, buffer, size);
}
/* Hooks */
// Event loop hook
void on_event_loop() {
    uint32_t current_time = now();
    if (current_time - last_timestamp_in_event_loop  > 1000000) {
        last_timestamp_in_event_loop = current_time;
        process_time();
    }
}

// Advertising setup hook
void on_adv_setup() {
    current_gap_role = GAP_ROLE_ADVERTISER;
}

#ifdef SCAN_ENABLED

// Scan-related hooks
void on_scan_rx_header() {
    current_gap_role = GAP_ROLE_SCANNER;
    process_scan_rx_header();
}

void on_scan_rx() {
    if (is_rx_done()) {
        current_gap_role = GAP_ROLE_SCANNER;
        process_scan_rx();
    }
}

#endif

#ifdef CONNECTION_ENABLED

// Connection-related hooks
void on_conn_rx_header() {
    process_conn_rx_header();
}

void on_conn_rx(void * ptr) {
    connection_structure = ptr;
    current_gap_role = (is_slave() ? GAP_ROLE_PERIPHERAL : GAP_ROLE_CENTRAL);

    if (connected == 0) {
        connected = 1;
        process_conn_init();
    }
    if (is_rx_done()) {
        process_conn_rx(false);
    }
}

void on_conn_delete(void * ptr) {
    connected = 0;
    process_conn_delete();
    connection_structure = ptr;
}

#endif
