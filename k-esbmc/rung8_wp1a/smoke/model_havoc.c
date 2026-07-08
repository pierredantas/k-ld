#include "bindings.h"
#include <stdlib.h>
/* Havoc timer (the ESBMC-PLC 'simple format' defect): the done bit / Light is
   left unconstrained -- free each scan, independent of Btn. This is what
   manufactures the false alarm on property A. */
int g_Btn = 0, g_Light = 0;
void model_init(void){ g_Btn = 0; g_Light = 0; }
void model_scan(void){ g_Light = rand() & 1; }
