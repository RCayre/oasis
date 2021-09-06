#include "time.h"
#include "functions.h"

uint32_t timestamp_in_us() {
  uint32_t t[2];
  btclk_GetNatClk_clkpclk(t);
  return btclk_Convert_clkpclk_us(t);
}
