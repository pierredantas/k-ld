// ctu_saturate: count-up to preset then saturate; reset dominant
CTU(CTU0_Q, 2, XIC(Pulse), XIC(Reset)) ;
OTE(Done) := XIC(CTU0_Q) ;
