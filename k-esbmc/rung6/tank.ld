OTE(PUMP) := XIC(AUTO_MODE) * XIC(LOW_SWITCH) * XIO(HIGH_SWITCH) * XIO(Draining_Active) ;
OTE(Filling_Active) := XIC(PUMP) ;
OTE(VALVE) := XIC(AUTO_MODE) * XIC(HIGH_SWITCH) * XIO(LOW_SWITCH) * XIO(Filling_Active) ;
OTE(Draining_Active) := XIC(VALVE) ;
