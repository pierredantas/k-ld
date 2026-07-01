// E1/E2 retention test: a set/reset latch on Q0.
//   Rung 1:  --| I0 |----( L Q0 )--   latch   Q0 when I0
//   Rung 2:  --| I1 |----( U Q0 )--   unlatch Q0 when I1
// Retention is the point: once latched, Q0 stays true across scans even after
// I0 drops, until I1 unlatches it.
OTL(Q0) := XIC(I0) ;
OTU(Q0) := XIC(I1) ;
