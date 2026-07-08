// edge_counter: rising edges feed a counter; reset dominant
OTE(Rise) := XIC(Sig) * XIO(Sig_prev) ;
CTU(Cnt_Q, 3, XIC(Rise), XIC(Reset)) ;
OTE(Full) := XIC(Cnt_Q) ;
OTE(Sig_prev) := XIC(Sig) ;
