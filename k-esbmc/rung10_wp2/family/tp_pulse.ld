// tp_pulse: pulse timer holds output through the pulse even if input drops
TP(TP0_Q, 3, XIC(Trig)) ;
OTE(Out) := XIC(TP0_Q) ;
