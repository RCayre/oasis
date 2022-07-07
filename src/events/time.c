#include "events.h"
#include "wrapper.h"
#include "types.h"
#include "metrics.h"
#include "timing.h"

#ifdef TIMING_MEASUREMENT
extern timing_measures_t timing_measures;
#endif

extern metrics_t metrics;

extern uint8_t time_callbacks_size;
extern callback_t time_callbacks[];

void process_time() {
    #ifdef TIMING_MEASUREMENT
    timing_measures.time_timestamp_start = now();
    #endif

    local_device_t* local_device = metrics.local_device;
    copy_own_bd_addr(local_device->address);
    local_device->gap_role = (gap_role_t)get_current_gap_role();

    #ifdef TIMING_MEASUREMENT
    timing_measures.time_timestamp_callbacks = now();
    #endif

    for(int i = 0; i < time_callbacks_size; i++) {
      time_callbacks[i](&metrics);
    }

    #ifdef TIMING_MEASUREMENT
    timing_measures.time_timestamp_end = now();
    report_timestamps(TIME_EVENT);
    #endif
}
