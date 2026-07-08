// Rung 4 pulse timer: a rising edge of IN (I0) emits a fixed PT-long pulse on
// T0, regardless of how IN behaves during the pulse; not retriggerable until IN
// goes low then high again.
TP(T0, 3, XIC(I0)) ;
