#include "bindings.h"
/* Faithful TON (MATIEC/K-ESBMC semantics): Q holds only while IN is high, and
   fires after PT scans measured from the rising edge. This is what MATIEC-C
   compiles to, so MATIEC-C+CBMC behaves like this model. */
int g_Btn = 0, g_Light = 0;
static int et = 0;
#define PT 2
void model_init(void){ g_Btn = 0; g_Light = 0; et = 0; }
void model_scan(void){
  if (g_Btn) { if (et < PT) et++; g_Light = (et >= PT); }
  else       { et = 0;            g_Light = 0; }
}
