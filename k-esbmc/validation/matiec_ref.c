/* Dynamic OpenPLC ground-truth harness: drives MATIEC's reference FB bodies
 * (the exact code OpenPLC runs) with controlled __CURRENT_TIME and the SAME
 * input traces as the K-ESBMC tests, then prints the Q trace for diffing.
 * Time unit = seconds; Delta t = 1 s per scan, PT = 3 s  (maps to K-ESBMC DT=1,PT=3).
 * NOTE: FB instances are zero-initialised ({0}) so the .flags field is clear --
 * exactly as OpenPLC instantiates them as zeroed globals. Uninitialised stack
 * garbage in .flags can set the FORCE bit and make __SET_VAR silently skip.
 */
#include "iec_std_lib.h"
#include "iec_std_FB.h"
#include <stdio.h>

TIME __CURRENT_TIME;          /* define the extern global the FBs read */
IEC_BOOL __DEBUG = 0;

static TIME secs(long s){ TIME t; t.tv_sec = s; t.tv_nsec = 0; return t; }

int main(void){
  { TON t = {0}; TON_init__(&t,0); t.PT.value = secs(3);
    int IN[]={1,1,1,1,0};
    printf("TON: ");
    for(int i=0;i<5;i++){ __CURRENT_TIME=secs(i+1); t.IN.value=IN[i]; TON_body__(&t);
      printf("%c,", t.Q.value?'T':'F'); }
    printf("\n"); }

  { TOF t = {0}; TOF_init__(&t,0); t.PT.value = secs(3);
    int IN[]={1,1,0,0,0,0};
    printf("TOF: ");
    for(int i=0;i<6;i++){ __CURRENT_TIME=secs(i+1); t.IN.value=IN[i]; TOF_body__(&t);
      printf("%c,", t.Q.value?'T':'F'); }
    printf("\n"); }

  { TP t = {0}; TP_init__(&t,0); t.PT.value = secs(3);
    int IN[]={0,1,1,1,0,1};
    printf("TP:  ");
    for(int i=0;i<6;i++){ __CURRENT_TIME=secs(i+1); t.IN.value=IN[i]; TP_body__(&t);
      printf("%c,", t.Q.value?'T':'F'); }
    printf("\n"); }

  { CTU t = {0}; CTU_init__(&t,0); t.PV.value = 2;
    int CU[]={0,1,1,0,1,1,0}, R[]={0,0,0,0,0,1,0};
    printf("CTU: ");
    for(int i=0;i<7;i++){ t.CU.value=CU[i]; t.R.value=R[i]; CTU_body__(&t);
      printf("%c,", t.Q.value?'T':'F'); }
    printf("\n"); }

  { CTD t = {0}; CTD_init__(&t,0); t.PV.value = 2;
    int CD[]={0,1,1,0,1,1,0}, LD[]={1,0,0,0,0,0,1};
    printf("CTD: ");
    for(int i=0;i<7;i++){ t.CD.value=CD[i]; t.LD.value=LD[i]; CTD_body__(&t);
      printf("%c,", t.Q.value?'T':'F'); }
    printf("\n"); }

  return 0;
}
