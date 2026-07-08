// timer_latch_mix: timer sets a latched alarm; ack clears it
TON(T0, 3, XIC(Trig)) ;
OTL(Alarm) := XIC(T0) ;
OTU(Alarm) := XIC(Ack) ;
