// Rung 5 count-down: C0 loads PV=2 on I1 (dominant), counts rising edges of I0
// down to 0. Q (image bit C0) := CV <= 0.
CTD(C0, 2, XIC(I0), XIC(I1)) ;
