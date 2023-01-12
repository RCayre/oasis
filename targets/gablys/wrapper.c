
#include "wrapper.h"
#include "events.h"
#include "malloc.h"

/* Constants and peripherals registers */
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

// NVMC registers
#define NVMC_READY ((uint32_t*)0x4001E400)
#define NVMC_CONFIG ((uint32_t*)0x4001E504)
#define NVMC_ERASEPAGE ((uint32_t*)0x4001E508)
#define NVMC_ERASEALL ((uint32_t*)0x4001E50C)
#define NVMC_ERASEPCR0 ((uint32_t*)0x4001E510)
#define NVMC_ERASEUICR ((uint32_t*)0x4001E514)

#define PERSISTENT_STORAGE ((uint32_t*)0x25e00)
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

/* Global variables used internally by the wrapper */
extern uint32_t CODE_START[];
extern uint32_t DATA_START[];
extern uint32_t DATA_SIZE[];

// Internal softdevice variables used by the wrapper
uint8_t *current_gap_role = (uint8_t *)0x200000a1;
uint8_t *interrupt_type = (uint8_t *)0x20000d7c;
uint8_t *interrupt_type_central = (uint8_t*)0x20000d7a;
uint32_t *hop_interval = (uint32_t*)0x20000ee4;

// action command field
uint32_t command = NO_COMMAND;

// Internals global variables used by the wrapper
static uint32_t millis = 0;

// NVMC control
void nvmc_erase_page(uint32_t address)
{
  // Enable erase.
  *NVMC_CONFIG = 2;
  while (*NVMC_READY == 0){}

  // Erase the page
  *NVMC_ERASEPAGE = address;
  while (*NVMC_READY == 0){}

  *NVMC_CONFIG = 0;
  while (*NVMC_READY == 0){}
}


void nvmc_write_byte(uint32_t address, uint8_t value)
{
  uint32_t byte_shift = address & (uint32_t)0x03;
  uint32_t address32 = address & ~byte_shift; // Address to the word this byte is in.
  uint32_t value32 = (*(uint32_t*)address32 & ~((uint32_t)0xFF << (byte_shift << (uint32_t)3)));
  value32 = value32 + ((uint32_t)value << (byte_shift << 3));

  // Enable write.
  *NVMC_CONFIG = 1;
  while (*NVMC_READY == 0){}

  *(uint32_t*)address32 = value32;
  while (*NVMC_READY == 0){}

  *NVMC_CONFIG = 0;
}

void nvmc_write_bytes(uint32_t address, uint8_t * src, uint32_t num_bytes)
{
  uint32_t i;
  for(i=0;i<num_bytes;i++)
  {
     nvmc_write_byte(address+i,src[i]);
  }
}

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
uint16_t connected = 0;
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
/* Generic Wrapper API */
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
    //*TIMER2_CC1 = 1;

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
/* Actions API */
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

uint32_t seconds = 0;

void log(uint8_t* buffer,uint8_t size) {
    memset(log_buffer,0x00,250);
    memcpy(log_buffer+2, buffer, size);
    log_buffer[0] = log_counter++;
    log_buffer[1] = size;
    int i=0;
    while (*(PERSISTENT_STORAGE+i) != 0xFFFFFFFF) {
      i++;
    }
    nvmc_write_bytes((PERSISTENT_STORAGE+i), &seconds, 4);
    nvmc_write_bytes(PERSISTENT_STORAGE+i+1, log_buffer+2, size);
}

/* Hooks */

// Event loop hook
void on_event_loop() {
    if (millis % 100 == 0) {
        process_time();
        seconds += 1;
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
    /*
    if (packet_flag_conn_tx == 1) {
        last_crc_ok = last_conn_crc_ok;
        last_timestamp = last_conn_timestamp;
        last_channel = last_conn_channel;
        process_conn_tx();
        packet_flag_conn_tx = 0;
    }
    */
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
    if (connected == 1 && (now() - last_conn_timestamp) > 1000000) {
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
    /*
    if (*TIMER2_EVENTCOMPARE1 != 0) {
        *TIMER2_EVENTCOMPARE1 = 0;
        on_event_loop();
    }
    */
}

// Initialization hook
void on_init() {
    uint32_t RAM_ZONE_START = (uint32_t)CODE_START - (uint32_t)DATA_SIZE;
    memcpy((void*)DATA_START, (void*)RAM_ZONE_START,(uint32_t)DATA_SIZE);
    timer2_init();
    //uint8_t a[] = {0x41,0x42,0x43,0x44};
    //nvmc_erase_page(PERSISTENT_STORAGE);

    //while (*(uint32_t*)(PERSISTENT_STORAGE+i) != 0xFFFFFFFF) i++;

    /*uint8_t log[4] = {0,0,0,0};
    nvmc_write_bytes(PERSISTENT_STORAGE+i, log, 4);*/
    //nvmc_erase_page(0x25e88);
    //uint8_t test[4] = {0x61,0x62, 0x63, 0x64 };
    //nvmc_write_bytes(0x25f48, test, 4);
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
