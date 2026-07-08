// tof_hold: off-delay holds the light after the sensor clears (stairs-like)
TOF(TOF0_Q, 5, XIC(Pir)) ;
OTE(Light) := XIC(TOF0_Q) + XIC(Button) ;
