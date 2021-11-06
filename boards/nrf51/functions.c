#include "functions.h"
#include "hooks.h"
#include "log.h"

/////////////////////////////////////////////////////////////////////
///////// *((uint32_t*)0x200000a1); FIRST BYTE SEEMS TO INDICATE THE GAP ROLE:
////////  01 : peripheral / 00 : advertiser / 02 : scanner / 03 : central
#define RX_TYPE 1
#define TX_TYPE 2

#define GAP_ROLE_ADVERTISER 0
#define GAP_ROLE_PERIPHERAL 1
#define GAP_ROLE_SCANNER    2
#define GAP_ROLE_CENTRAL    3

//#define RAM_DATA_START (void*)0x20002A80
//#define DATA_START (void*)0x23048
//#define CODE_START (void*)&BASE_FLASH
uint8_t *gap_role = (uint8_t *)0x200000A1;
uint8_t *isr_type = (uint8_t *)0x20000d7c;

extern uint32_t CODE_START[];
extern uint32_t RAM_START[];
extern uint32_t RAM_LENGTH[];
/**
 * Hooks
 */
uint8_t packet[100] ;
static int millis = 0;

uint32_t * timer2_mode = (uint32_t *)0x4000A504;
uint32_t * timer2_width = (uint32_t *)0x4000A508;
uint32_t * timer2_prescaler = (uint32_t *)0x4000A510;
uint32_t * timer2_intenset = (uint32_t *)0x4000A304;
uint32_t * timer2_intenclr = (uint32_t *)0x4000A308;
uint32_t * timer2_clear = (uint32_t *)0x4000A00c;
uint32_t * timer2_start = (uint32_t *)0x4000A000;
uint32_t * timer2_capture0 = (uint32_t *)0x4000A040;
uint32_t * timer2_cc0 = (uint32_t *)0x4000A540;

uint32_t * timer2_shorts = (uint32_t *)0x4000A200;

uint32_t * timer2_capture1 = (uint32_t *)0x4000A048;
uint32_t * timer2_cc1 = (uint32_t *)0x4000A548;

uint32_t * timer2_eventcompare0 = (uint32_t *)0x4000A140;
uint32_t * timer2_eventcompare1 = (uint32_t *)0x4000A144;
uint32_t * nvic_enableirq = (uint32_t *)0xe000e100;
uint32_t * nvic_clearpendingirq = (uint32_t *)0xe000e280;
uint32_t * nvic_disableirq = (uint32_t *)0xe000e408;

uint32_t * nvic_test = (uint32_t *)0xe000e408;

uint32_t * radio_frequency = (uint32_t *)0x40001508;
uint32_t * radio_shorts = (uint32_t *)0x40001200;
uint32_t * radio_state = (uint32_t *)0x40001550;
uint32_t * radio_crcok = (uint32_t *)0x40001400;
uint32_t * radio_eventend = (uint32_t *)0x4000110C;
uint32_t * radio_packetptr = (uint32_t *)0x40001504;

void TIMER2_IRQHandler(void) {
  if (*timer2_eventcompare0 != 0) {
    *timer2_eventcompare0 = 0;
    millis++;
  }
}

void timer2_init() {


  //if ((*nvic_test >> 0xe & 1) != 0) {

  //}


  *timer2_intenset = 0x10000;
  *timer2_mode = 0;
  *timer2_width = 0;

  *timer2_prescaler = 4;
  *timer2_shorts = 1;
  *timer2_cc0 = 10000;

  *nvic_disableirq = *nvic_disableirq & 0xff00ffff | 0x400000;

  *nvic_clearpendingirq = 0x400;
//  if (*(nrf_nvic_state+4) == 0) {
    *nvic_enableirq = 0x400;
//  }
  //else {
    //*nrf_nvic_state = *nrf_nvic_state | 0x400;
  //}
  *timer2_start = 1;
  *timer2_clear = 1;


}

void on_init() {
  uint32_t DATA_START = (uint32_t)CODE_START - (uint32_t)RAM_LENGTH;
  memcpy((void*)RAM_START, (void*)DATA_START,(uint32_t)RAM_LENGTH);
  timer2_init();

}
uint32_t data_pcnf = 0;
uint8_t packetflag = 0;
void on_isr() {
  if (*radio_eventend == 1) {
    if (*isr_type == RX_TYPE) {
      if ((*gap_role == GAP_ROLE_ADVERTISER || *gap_role == GAP_ROLE_SCANNER) && is_crc_good() && packetflag == 0) {
        packetflag = 1;
        memcpy(packet,*radio_packetptr,2);
        if (packet[1] > 0) {
          memcpy(&packet[2],*radio_packetptr+3,packet[1]);
        }
        process_scan_rx_header();
        process_scan_rx();
        packetflag = 0;
      }
      else {
        //process_conn_rx_header();
        //process_conn_rx(1);
      }
    }

  }
}
__attribute__((optimize("O0")))
__attribute__((naked))
uint32_t sd_ble_gap_scan_stop() {
  __asm__("svc 0x8b");
}

/**@brief GAP scanning parameters. */
typedef struct
{
  uint8_t                 active    : 1;        /**< If 1, perform active scanning (scan requests). */
  uint8_t                 selective : 1;        /**< If 1, ignore unknown devices (non whitelisted). */
  uint32_t *   p_whitelist;          /**< Pointer to whitelist, NULL if no whitelist or the current active whitelist is to be used. */
  uint16_t                interval;             /**< Scan interval between 0x0004 and 0x4000 in 0.625ms units (2.5ms to 10.24s). */
  uint16_t                window;               /**< Scan window between 0x0004 and 0x4000 in 0.625ms units (2.5ms to 10.24s). */
  uint16_t                timeout;              /**< Scan timeout between 0x0001 and 0xFFFF in seconds, 0x0000 disables timeout. */
} ble_gap_scan_params_t;

uint32_t sd_ble_gap_scan_start(ble_gap_scan_params_t* p_scan_params) {
  __asm__("svc 0x8a");
}

ble_gap_scan_params_t m_scan_param =
{
    0,
    0,
    NULL,
    (uint16_t)0x00A0,
    (uint16_t)0x0050,
    0x0000
};

void run_scan() {
  //sd_ble_gap_scan_stop();
  sd_ble_gap_scan_start(&m_scan_param);
}
uint32_t toto = 0;
uint32_t access_address = 0;
void on_set_access_address(uint32_t *access_address_ptr) {
    memcpy(&access_address,access_address_ptr,4);
    if (access_address != 0x8e89bed6 && toto == 0){
       toto++;
       //run_scan();
     }
}

void on_event_loop() {
  /*
  if (toto == 1) {
    //run_scan();
    toto++;
  }*/
}
uint32_t crc_init = 0;
void on_set_crc_init(uint32_t *crc_init_ptr) {
  memcpy(&crc_init,crc_init_ptr,3);
}

uint8_t channel_map[5] = {0,0,0,0,0};
void on_set_channel_map(void *channel_map1,void *channel_map2) {
  memcpy(channel_map,channel_map2,5);
}

uint8_t adv_address[6] = {0,0,0,0,0,0};
void on_set_adv_address(void *addr,void *addr2) {
  memcpy(adv_address,addr2,6);
}


/**
 * API implementation
 */

void * memcpy(void * dst, void * src, uint32_t size) {
	for (int i=0;i<size;i++) {
		*(uint8_t*)(dst+i) = *(uint8_t*)(src+i);
	}
}
uint8_t log_buffer[250];
uint8_t log_pointer = 0;
void send_hci(uint8_t opcode, void * content, uint32_t size) {
  memcpy(log_buffer,content, size);
}

uint32_t get_timestamp_in_us() {
    *timer2_capture1 = 1;
    return *timer2_cc1+millis*10000;
}        //for (int i=0;i<40;i++) rx[i] = 0;


int get_rssi() {
    return 0;
}

void copy_header(uint8_t * dst) {
  memcpy(dst,packet,2);

}

bool is_rx_done() {
    return *radio_eventend == 1;
}

void copy_own_adv_addr(uint8_t * dst) {
  memcpy(dst, adv_address,6);
}

uint8_t get_channel() {
  uint8_t channel = 0;
  uint32_t frequency = *(uint32_t*)radio_frequency;
  if (frequency == 2) channel = 37;
  else if (frequency == 26) channel = 38;
  else if (frequency == 80) channel = 39;
  else if (frequency < 24) channel = (frequency/2) - 2;
  else channel = (frequency/2) - 3;
  return channel;
}


void copy_buffer(uint8_t * dst, uint8_t size) {
  memcpy(dst,&packet[2],size);
}

bool is_slave() {
  return *gap_role == GAP_ROLE_PERIPHERAL;
}

void copy_channel_map(uint8_t * dst) {
  memcpy(dst,channel_map,5);
}

uint16_t get_hop_interval() {
  return 0;
}

uint32_t get_crc_init() {
  return crc_init;
}

void copy_access_addr(uint8_t * dst) {
  memcpy(dst,&access_address,4);
}

bool is_crc_good() {
  return *radio_crcok == 1;
}

void launch_hci_command(uint16_t opcode, uint8_t * buffer, uint8_t size) {

}
