// Rung 5 count-up: C0 counts rising edges of I0 up to PV=2; I1 resets (dominant).
// Q (image bit C0) := CV >= PV.
CTU(C0, 2, XIC(I0), XIC(I1)) ;
