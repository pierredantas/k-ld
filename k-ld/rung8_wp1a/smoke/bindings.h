#ifndef BINDINGS_H
#define BINDINGS_H
/* The single per-benchmark integration point. For the real WP1a run this maps
   VAR(x) onto MATIEC's generated located variable for x and model_scan() onto
   config_run__(); here it maps onto the hand-written scan model below. */
extern int g_Btn, g_Light;
void model_init(void);
void model_scan(void);
#define IN(x)  g_##x
#define OUT(x) g_##x
#define VAR(x) g_##x
#endif
