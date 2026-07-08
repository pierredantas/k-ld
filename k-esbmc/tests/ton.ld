// Rung 4 timer test: on-delay timer T0, preset PT=3 time units, IN = I0.
// The done bit T0 (exposed in the image) must go true only after I0 has been
// continuously true for PT, and reset when I0 drops.
TON(T0, 3, XIC(I0)) ;
