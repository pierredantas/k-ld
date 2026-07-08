// ton_chain2: chain of two on-delay timers -> mutually exclusive phases
TON(T1, 2, XIC(Enable)) ;
TON(T2, 2, XIC(T1)) ;
OTE(P1) := XIC(Enable) * XIO(T1) ;
OTE(P2) := XIC(T1) * XIO(T2) ;
