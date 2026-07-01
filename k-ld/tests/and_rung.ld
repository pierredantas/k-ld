// E1 micro-test: series contacts (AND) driving a coil.
// Rung:  --| I0 |--| I1 |----( Q0 )--
// OTE(Q0) is TRUE iff I0 AND I1.
OTE(Q0) := XIC(I0) * XIC(I1) ;
