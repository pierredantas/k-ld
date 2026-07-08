/* CBMC harness over REAL MATIEC-generated C (config.c/res.c/POUS.c). Drives the
   program instance's Btn nondeterministically each scan and checks property A. */
#include "iec_std_lib.h"
#include "POUS.h"
extern PROG RES__INST;
extern void config_init__(void);
extern void config_run__(unsigned long tick);
int nondet_bool(void);
int main(void){
  config_init__();
  unsigned long tick = 0;
  for (int s = 0; s < 6; s++){
    RES__INST.BTN.value = nondet_bool();
    config_run__(tick++);
    __CPROVER_assert(!RES__INST.LIGHT.value || RES__INST.BTN.value, "prop A: !Light || Btn");
  }
  return 0;
}
