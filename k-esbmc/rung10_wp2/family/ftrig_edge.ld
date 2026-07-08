// ftrig_edge: falling-edge one-shot (F_TRIG lowering)
OTE(Fall) := XIO(Sig) * XIC(Sig_prev) ;
OTE(OneShot) := XIC(Fall) ;
OTE(Sig_prev) := XIC(Sig) ;
