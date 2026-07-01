OTE(System_Running) := XIC(Start_Button) * XIO(Emergency_Stop) * XIO(Stop_Button) ;
OTE(Fill_Valve) := XIC(System_Running) * XIO(Filling_Done) ;
OTE(TON1_IN) := XIC(Fill_Valve) ;
TON(TON1_Q, 2, XIC(TON1_IN)) ;
OTE(Filling_Done) := XIC(TON1_Q) ;
OTE(Filling_Active) := XIC(Fill_Valve) ;
OTE(Conveyor_Motor) := XIC(Filling_Done) * XIC(Conveyor_Ready) ;
OTE(Alarm_Overfill) := XIC(Level_Full) * XIC(Fill_Valve) ;
OTE(Alarm_No_Bottle) := XIC(Fill_Valve) * XIO(Bottle_Present) ;
