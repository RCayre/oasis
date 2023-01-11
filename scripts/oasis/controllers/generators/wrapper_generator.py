from string import Template

WRAPPER_INCLUDES = """
#include "wrapper.h"
#include "events.h"
#include "malloc.h"
"""


BROADCOM_WRAPPER_HEADER = """
#define GAP_ROLE_ADVERTISER 0
#define GAP_ROLE_PERIPHERAL 1
#define GAP_ROLE_SCANNER    2
#define GAP_ROLE_CENTRAL    3

#ifdef CONNECTION_ENABLED

uint8_t IS_SLAVE_OFFSET = $is_slave_offset;
uint8_t CHANNEL_OFFSET = $channel_offset;
uint8_t SECOND_STRUCT_OFFSET = $second_struct_offset;
uint8_t HOP_INTERVAL_OFFSET_IN_SECOND_STRUCT = $hop_interval_offset;
uint8_t CHANNEL_MAP_OFFSET_IN_SECOND_STRUCT = $channel_map_offset;
uint8_t CRC_INIT_OFFSET_IN_SECOND_STRUCT = $crc_init_offset;
uint8_t ACCESS_ADDR_OFFSET_IN_SECOND_STRUCT = $access_address_offset;

#endif
"""

BROADCOM_WRAPPER_REGISTERS = """
uint8_t * rx_header_register = (uint8_t *) $rx_header_register;
uint8_t * rx_register = (uint8_t *) $rx_register;
uint8_t * status_register = (uint8_t *) $status_register;
uint8_t * channel = (uint8_t *) $channel;
uint8_t * hci_callbacks_table = (uint8_t *) $hci_callbacks_table;
uint8_t * bd_address = (uint8_t *) $bd_address;
"""

BROADCOM_WRAPPER_GLOBALS_VARIABLES = """
uint8_t current_gap_role;
void *connection_structure;
uint32_t last_timestamp_in_event_loop;
uint8_t connected = 0;

"""

BROADCOM_WRAPPER_GENERIC_API = """
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
"""

BROADCOM_WRAPPER_OLD_HCI_API = """
void send_hci_event(uint8_t opcode, void * content, uint32_t size) {
    char *hci_buffer = bthci_event_AllocateEventAndFillHeader(opcode, size + 2);
    memcpy(hci_buffer + 2, content, size);
    bthci_event_AttemptToEnqueueEventToTransport(hci_buffer);
    bthci_event_FreeEvent(hci_buffer);
}

void run_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size) {
    uint8_t param[size + 3];
    param[0] = opcode & 0xFF;
    param[1] = (opcode & 0xFF00) >> 8;
    param[2] = size;

    // Copy the hci command parameter
    memcpy(param + 3, buffer, size);

    uint8_t error_code;
    void (*handler)(uint8_t *error_code,uint8_t * buffer) = (void*)*(uint32_t *)(hci_callbacks_table + opcode*4);
    handler(&error_code,param);
}
"""

BROADCOM_WRAPPER_NEW_HCI_API = """
void send_hci_event(uint8_t opcode, void * content, uint32_t size) {
    char *hci_buffer = bthci_event_AllocateEventAndFillHeader(size + 2, opcode, size);
    memcpy(hci_buffer + 10, content, size);
    bthci_event_AttemptToEnqueueEventToTransport(hci_buffer);
}

void run_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size) {
    uint8_t param[size + 11];
    // Set first 11 bytes to 0
    for(uint8_t i = 0; i < 12; i++) {
    param[i] = 0;
    }
    param[8] = 0x01;
    param[9] = (uint8_t)(opcode & 0xFF);
    param[10] = 0x20;
    param[11] = size;
    // Copy the hci command parameter
    memcpy(param + 12, buffer, size);

    void (*handler)(uint8_t * buffer) = (void*)*(uint32_t *)(hci_callbacks_table + (opcode << 3) - 8);
    handler(param);
}
"""

BROADCOM_WRAPPER_ACTIONS_API = """
void start_scan() {
    uint8_t buffer[2];
    buffer[0] = 1;
    buffer[1] = 1;
    run_hci_command(0xc, buffer, 2);
}

void stop_scan() {
    uint8_t buffer[2];
    buffer[0] = 0;
    buffer[1] = 1;
    run_hci_command(0xc, buffer, 2);
}

void log(uint8_t *buffer, uint8_t size) {
    send_hci_event(0xFF, buffer, size);
}
"""

BROADCOM_WRAPPER_HOOKS = """
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
}

#endif
"""

NRF51_SOFTDEVICE_WRAPPER_HEADER = """
// Radio interruption type constants
#define RX_TYPE 1
#define TX_TYPE 2

// Gap roles constants
#define GAP_ROLE_ADVERTISER 0
#define GAP_ROLE_PERIPHERAL 1
#define GAP_ROLE_SCANNER    2
#define GAP_ROLE_CENTRAL    3

// Actions command constants
#define NO_COMMAND  0
#define START_SCAN  1
#define STOP_SCAN   2

// Peripherals registers
#define TIMER2_MODE ((uint32_t*)0x4000A504)
#define TIMER2_WIDTH ((uint32_t*)0x4000A508)
#define TIMER2_PRESCALER ((uint32_t*)0x4000A510)
#define TIMER2_INTENSET ((uint32_t*)0x4000A304)
#define TIMER2_INTENCLR ((uint32_t*)0x4000A308)
#define TIMER2_CLEAR ((uint32_t*)0x4000A00c)
#define TIMER2_START ((uint32_t*)0x4000A000)
#define TIMER2_SHORTS ((uint32_t*)0x4000A200)

#define TIMER2_CAPTURE0 ((uint32_t*)0x4000A040)
#define TIMER2_CC0 ((uint32_t*)0x4000A540)

#define TIMER2_CAPTURE1 ((uint32_t*)0x4000A044)
#define TIMER2_CC1 ((uint32_t*)0x4000A544)

#define TIMER2_CAPTURE2 ((uint32_t*)0x4000A048)
#define TIMER2_CC2 ((uint32_t*)0x4000A548)

#define TIMER2_EVENTCOMPARE0 ((uint32_t*)0x4000A140)
#define TIMER2_EVENTCOMPARE1 ((uint32_t*)0x4000A144)
#define TIMER2_EVENTCOMPARE2 ((uint32_t*)0x4000A148)

#define NVIC_ENABLEIRQ ((uint32_t*)0xe000e100)
#define NVIC_CLEARPENDINGIRQ ((uint32_t*)0xe000e280)
#define NVIC_DISABLEIRQ ((uint32_t*)0xe000e408)
#define NVIC_TEST ((uint32_t*)0xe000e408)

#define RADIO_RSSI ((uint32_t*)0x40001548)
#define RADIO_FREQUENCY ((uint32_t*)0x40001508)
#define RADIO_SHORTS ((uint32_t*)0x40001200)
#define RADIO_STATE ((uint32_t*)0x40001550)
#define RADIO_CRCOK ((uint32_t*)0x40001400)
#define RADIO_EVENTEND ((uint32_t*)0x4000110C)
#define RADIO_PACKETPTR ((uint32_t*)0x40001504)

// Type definitions
typedef struct
{
  uint8_t active    : 1;
  uint8_t selective : 1;
  uint32_t *p_whitelist;
  uint16_t interval;
  uint16_t window;
  uint16_t timeout;
} ble_gap_scan_params_t;

"""

NRF51_SOFTDEVICE_WRAPPER_GLOBAL_VARIABLES = """
extern uint32_t CODE_START[];
extern uint32_t DATA_START[];
extern uint32_t DATA_SIZE[];

// Internal softdevice variables used by the wrapper
uint8_t *current_gap_role = (uint8_t *)$gap_role;
uint8_t *interrupt_type = (uint8_t *)$interrupt_type;
uint8_t *interrupt_type_central = (uint8_t*)$interrupt_type_central;
uint32_t *hop_interval = (uint32_t*)$hop_interval;

// action command field
uint32_t command = NO_COMMAND;

// Internals global variables used by the wrapper
static uint32_t millis = 0;

#ifdef SCAN_ENABLED
uint8_t last_scan_channel = 0;
bool last_scan_crc_ok = 0;
uint32_t last_scan_timestamp = 0;

uint8_t packet_flag_scan_rx = 0;
uint8_t tmp_scan_buffer[128];

#endif

#ifdef CONNECTION_ENABLED
uint8_t last_conn_channel = 0;
bool last_conn_crc_ok = 0;
uint32_t last_conn_timestamp = 0;

uint8_t packet_flag_conn_rx = 0;
uint8_t tmp_conn_buffer[128];

#endif

uint8_t rssi = 0;

uint8_t last_channel = 0;
bool last_crc_ok = 0;
uint32_t last_timestamp = 0;

uint8_t *tmp_buffer = 0;

#ifdef CONNECTION_ENABLED
uint32_t access_address = 0;
uint32_t crc_init = 0;
uint8_t channel_map[5] = {0,0,0,0,0};
uint32_t connected = 0;
#endif

uint8_t bd_address[6] = {0,0,0,0,0,0};

uint8_t log_buffer[250];
uint8_t log_counter = 0;

ble_gap_scan_params_t scan_parameters =
{
    0,
    0,
    NULL,
    (uint16_t)0x00A0,
    (uint16_t)0x0050,
    0x0000
};
"""

NRF51_SOFTDEVICE_WRAPPER_API = """
// Utilities functions
void * memcpy(void * dst, void * src, uint32_t size) {
	for (int i=0;i<size;i++) {
		*(uint8_t*)(dst+i) = *(uint8_t*)(src+i);
	}
}

void * memset(void * dst, uint8_t value, uint32_t size) {
	for (int i=0;i<size;i++) {
		*(uint8_t*)(dst+i) = value;
	}
}

// Time-related functions
void timer2_init() {
    *TIMER2_INTENSET = 0x10000;
    *TIMER2_MODE = 0;
    *TIMER2_WIDTH = 0;

    *TIMER2_PRESCALER = 4;
    *TIMER2_SHORTS = 1;
    *TIMER2_CC0 = 10000;

    *NVIC_DISABLEIRQ = *NVIC_DISABLEIRQ & 0xff00ffff | 0x400000;

    *NVIC_CLEARPENDINGIRQ = 0x400;
    *NVIC_ENABLEIRQ = 0x400;

    *TIMER2_START = 1;
    *TIMER2_CLEAR = 1;
}

uint32_t get_timestamp() {
    *TIMER2_CAPTURE2 = 1;
    return *TIMER2_CC2+millis*10000;
}

uint32_t now() {
    return get_timestamp();
}

uint32_t get_timestamp_in_us() {
    return last_timestamp;
}

// Packet-related functions

bool get_crc() {
    return *RADIO_CRCOK == 1;
}

bool is_crc_good() {
    return last_crc_ok;
}

int get_rssi() {
    return rssi;
}

void copy_header(uint8_t * dst) {
    memcpy(dst,tmp_buffer,2);
}

bool is_rx_done() {
    return *RADIO_EVENTEND == 1;
}

void copy_buffer(uint8_t * dst, uint8_t size) {
    memcpy(dst,&tmp_buffer[3],size);
}

// Multi-role functions

uint8_t get_current_channel() {
    uint8_t channel = 0;
    uint32_t frequency = *(uint32_t*)RADIO_FREQUENCY;
    if (frequency == 2) channel = 37;
    else if (frequency == 80) channel = 39;
    else if (frequency == 26) channel = 38;
    else if (frequency < 24) channel = (frequency/2) - 2;
    else channel = (frequency/2) - 3;
    return channel;
}

void copy_own_bd_addr(uint8_t * dst) {
    memcpy(dst, bd_address,6);
}

uint8_t get_channel() {
    return last_channel;
}

uint8_t get_current_gap_role() {
    return *current_gap_role;
}

// Connection-related functions
#ifdef CONNECTION_ENABLED
bool is_slave() {
    return *current_gap_role == GAP_ROLE_PERIPHERAL;
}

void copy_channel_map(uint8_t * dst) {
    memcpy(dst,channel_map,5);
}

uint16_t get_hop_interval() {
    return *hop_interval >> 8;
}

uint32_t get_crc_init() {
    return crc_init;
}

void copy_access_addr(uint32_t * dst) {
    memcpy(dst,&access_address,4);
}
#endif
"""


NRF51_SOFTDEVICE_WRAPPER_ACTIONS_API = """
uint32_t sd_ble_gap_scan_start(ble_gap_scan_params_t* p_scan_params) {
    __asm__("svc 0x8a");
}

__attribute__((optimize("O0")))
__attribute__((naked))
uint32_t sd_ble_gap_scan_stop() {
    __asm__("svc 0x8b");
}

void start_scan() {
    command = START_SCAN;
}

void stop_scan() {
    command = STOP_SCAN;
}


void log(uint8_t* buffer,uint8_t size) {
    memset(log_buffer,0x00,250);
    memcpy(log_buffer+2, buffer, size);
    log_buffer[0] = log_counter++;
    log_buffer[1] = size;
}

"""

NRF51_SOFTDEVICE_WRAPPER_HOOKS = """

// Event loop hook

void on_event_loop() {
    if (millis % 100 == 0) {
        process_time();
    }
    #ifdef SCAN_ENABLED
    if (packet_flag_scan_rx == 1) {
        tmp_buffer = &tmp_scan_buffer[0];
        last_crc_ok = last_scan_crc_ok;
        last_timestamp = last_scan_timestamp;
        last_channel = last_scan_channel;

        process_scan_rx_header();
        process_scan_rx();
        packet_flag_scan_rx = 0;
    }
    #endif
    #ifdef CONNECTION_ENABLED
    if (packet_flag_conn_rx == 1) {
        if (connected == 0) {
          connected = 1;
          process_conn_init();
        }
        tmp_buffer = &tmp_conn_buffer[0];
        last_crc_ok = last_conn_crc_ok;
        last_timestamp = last_conn_timestamp;
        last_channel = last_conn_channel;

        process_conn_rx_header();
        process_conn_rx(true);
        packet_flag_conn_rx = 0;
    }
    if (connected == 1 && (now() - last_conn_timestamp) > 100000) {
        process_conn_delete();
        connected = 0;
    }
    #endif
    if (command == START_SCAN) {
        sd_ble_gap_scan_start(&scan_parameters);
        command = NO_COMMAND;
    }

    else if (command == STOP_SCAN) {
        sd_ble_gap_scan_stop();
        command = NO_COMMAND;
    }
}

// Timer2 interrupt hook
void on_timer_interrupt() {
    if (*TIMER2_EVENTCOMPARE0 != 0) {
        *TIMER2_EVENTCOMPARE0 = 0;
        millis++;
    }
}

// Initialization hook
void on_init() {
    uint32_t RAM_ZONE_START = (uint32_t)CODE_START - (uint32_t)DATA_SIZE;
    memcpy((void*)DATA_START, (void*)RAM_ZONE_START,(uint32_t)DATA_SIZE);
    timer2_init();
}

#ifdef CONNECTION_ENABLED
// Connection initialization hook
void on_init_connection() {
}
#endif

// Radio interrupt hook
void on_radio_interrupt() {
    if (*RADIO_EVENTEND == 1) {
        #ifdef SCAN_ENABLED
        if ((*current_gap_role == GAP_ROLE_ADVERTISER || *current_gap_role == GAP_ROLE_SCANNER)) {
            if (packet_flag_scan_rx == 0) {
                packet_flag_scan_rx = 1;
                last_scan_timestamp = get_timestamp();
                last_scan_crc_ok = get_crc();
                last_scan_channel = get_current_channel();
                rssi = *RADIO_RSSI;
                memcpy(tmp_scan_buffer,(void*)*RADIO_PACKETPTR,40);
            }
        }
        #endif
        #ifdef CONNECTION_ENABLED
        if ((*current_gap_role == GAP_ROLE_CENTRAL || *current_gap_role == GAP_ROLE_PERIPHERAL)) {
            if (packet_flag_conn_rx == 0 && (*current_gap_role == GAP_ROLE_CENTRAL && *interrupt_type_central == 2) || *interrupt_type == RX_TYPE) {
                packet_flag_conn_rx = 1;
                last_conn_timestamp = get_timestamp();
                last_conn_crc_ok = get_crc();
                last_conn_channel = get_current_channel();
                rssi = *RADIO_RSSI;
                memcpy(tmp_conn_buffer,(void*)*RADIO_PACKETPTR,25);
            }
            /*
            if (packet_flag_conn_tx == 0 && (*current_gap_role == GAP_ROLE_CENTRAL && *interrupt_type_central == 1) || *interrupt_type == TX_TYPE) {
            packet_flag_conn_tx = 1;
            last_conn_timestamp = get_timestamp();
            last_conn_channel = get_current_channel();
            }
            */
        }
        #endif
    }
}

// Setters hooks
#ifdef CONNECTION_ENABLED
void on_set_crc_init(uint32_t *crc_init_ptr) {
    memcpy(&crc_init,crc_init_ptr,3);
}

void on_set_channel_map(void *channel_map1,void *channel_map2) {
    memcpy(channel_map,channel_map2,5);
}


void on_set_access_address(uint32_t *access_address_ptr) {
    memcpy(&access_address,access_address_ptr,4);
}
#endif

void on_set_bd_address(void *addr,void *addr2) {
    if (*current_gap_role != GAP_ROLE_SCANNER) {
        memcpy(bd_address,addr2,6);
    }
}

"""

NRF52_ZEPHYR_WRAPPER_HEADER = """
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

"""

NRF52_ZEPHYR_WRAPPER_GLOBALS_VARIABLES_NO_HCI_SUPPORT = """
uint8_t log_buffer[250];
uint8_t log_counter = 0;
"""

NRF52_ZEPHYR_WRAPPER_GLOBALS_VARIABLES_HCI_SUPPORT = """
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

"""

NRF52_ZEPHYR_WRAPPER_API = """
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

"""

NRF52_ZEPHYR_WRAPPER_ACTIONS_API_NO_HCI_SUPPORT = """
void start_scan() {
    // TODO: not implemented
}

void stop_scan() {
    // TODO: not implemented
}


void log(uint8_t* buffer,uint8_t size) {
    memset(log_buffer,0x00,250);
    memcpy(log_buffer+2, buffer, size);
    log_buffer[0] = log_counter++;
    log_buffer[1] = size;
}
"""

NRF52_ZEPHYR_WRAPPER_ACTIONS_API_HCI_SUPPORT = """
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
"""


NRF52_ZEPHYR_WRAPPER_COMMON_HOOKS = """
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

"""

NRF52_ZEPHYR_WRAPPER_CENTRAL_HOOKS = """
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

"""


NRF52_ZEPHYR_WRAPPER_PERIPHERAL_HOOKS = """
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
"""

NRF52_ZEPHYR_WRAPPER_CONNECTION_HOOKS = """
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
"""


NRF52_ZEPHYR_WRAPPER_SCAN_HOOKS = """
#ifdef SCAN_ENABLED
// Scan Reception hook
void on_scan() {
    process_scan_rx_header();
    process_scan_rx();
}
#endif
"""


def generateIncludes():
    return WRAPPER_INCLUDES

def generateComment(comment):
    return "/* "+ comment +" */"

def generateBroadcomWrapperHeader(offsets):
    template = Template(BROADCOM_WRAPPER_HEADER)
    return template.substitute(**offsets)

def generateNrf51SoftdeviceWrapperHeader():
    return NRF51_SOFTDEVICE_WRAPPER_HEADER

def generateNrf52ZephyrWrapperHeader():
    return NRF52_ZEPHYR_WRAPPER_HEADER

def generateFunctionSignature(function,returnValue, parameters):
    return returnValue+" "+function+" ("+parameters+");"

def generateBroadcomWrapperRegisters(registers):
    template = Template(BROADCOM_WRAPPER_REGISTERS)
    return template.substitute(**registers)

def generateBroacomWrapperGlobalsVariables():
    return BROADCOM_WRAPPER_GLOBALS_VARIABLES

def generateNrf51SoftdeviceWrapperGlobalsVariables(variables):
    template = Template(NRF51_SOFTDEVICE_WRAPPER_GLOBAL_VARIABLES)
    return template.substitute(**{k:hex(v) for k,v in variables.items()})

def generateNrf52ZephyrWrapperGlobalsVariables(hci_support=False):
    return (NRF52_ZEPHYR_WRAPPER_GLOBALS_VARIABLES_NO_HCI_SUPPORT if not hci_support else "") + NRF52_ZEPHYR_WRAPPER_GLOBALS_VARIABLES_HCI_SUPPORT

def generateBroadcomGenericAPI():
    return BROADCOM_WRAPPER_GENERIC_API

def generateNrf51SoftdeviceWrapperAPI():
    return NRF51_SOFTDEVICE_WRAPPER_API

def generateNrf52ZephyrWrapperAPI():
    return NRF52_ZEPHYR_WRAPPER_API

def generateBroadcomNewHciAPI():
    return BROADCOM_WRAPPER_NEW_HCI_API

def generateBroadcomOldHciAPI():
    return BROADCOM_WRAPPER_OLD_HCI_API

def generateBroadcomWrapperActionsAPI():
    return BROADCOM_WRAPPER_ACTIONS_API

def generateNrf51SoftdeviceWrapperActionsAPI():
    return NRF51_SOFTDEVICE_WRAPPER_ACTIONS_API

def generateNrf52ZephyrWrapperActionsAPI(hci_support=False):
    return NRF52_ZEPHYR_WRAPPER_ACTIONS_API_NO_HCI_SUPPORT if not hci_support else NRF52_ZEPHYR_WRAPPER_ACTIONS_API_HCI_SUPPORT

def generateBroadcomWrapperHooks():
    return BROADCOM_WRAPPER_HOOKS

def generateNrf51SoftdeviceWrapperHooks():
    return NRF51_SOFTDEVICE_WRAPPER_HOOKS

def generateNrf52ZephyrWrapperHooks(firmwareInformations):
    hooks = NRF52_ZEPHYR_WRAPPER_COMMON_HOOKS
    if firmwareInformations["scanner"]:
        hooks += NRF52_ZEPHYR_WRAPPER_SCAN_HOOKS
    if firmwareInformations["central"]:
        hooks += NRF52_ZEPHYR_WRAPPER_CENTRAL_HOOKS
    if firmwareInformations["peripheral"]:
        hooks += NRF52_ZEPHYR_WRAPPER_PERIPHERAL_HOOKS
    if firmwareInformations["peripheral"] or firmwareInformations["central"]:
        hooks += NRF52_ZEPHYR_WRAPPER_CONNECTION_HOOKS
    return hooks
