// rtrig_edge: rising-edge one-shot (R_TRIG lowering)
OTE(Rise) := XIC(Sig) * XIO(Sig_prev) ;
OTE(OneShot) := XIC(Rise) ;
OTE(Sig_prev) := XIC(Sig) ;
