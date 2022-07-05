#include "events.h"
#include "wrapper.h"
#include "types.h"
#include "metrics.h"
#include "timing.h"

extern timing_measures_t timing_measures;
extern metrics_t metrics;

extern uint8_t time_callbacks_size;
extern callback_t time_callbacks[];

void process_time() {
    timing_measures.time_timestamp_start = now();

    local_device_t* local_device = metrics.local_device;
    copy_own_bd_addr(local_device->address);
    local_device->gap_role = (gap_role_t)get_current_gap_role();

    timing_measures.time_timestamp_callbacks = now();
    for(int i = 0; i < time_callbacks_size; i++) {
      time_callbacks[i](&metrics);
    }
    timing_measures.time_timestamp_end = now();
    report_timestamps(TIME_EVENT);
}
