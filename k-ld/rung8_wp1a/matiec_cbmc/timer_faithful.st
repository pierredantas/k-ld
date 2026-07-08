(* Faithful scan-counting TON: fires after PT scans of continuous IN, drops when
   IN low -- the exact standard/K-LD state machine, PT counted in scans. *)
FUNCTION_BLOCK TON_scan
  VAR_INPUT IN : BOOL; PT : INT; END_VAR
  VAR_OUTPUT Q : BOOL; END_VAR
  VAR et : INT; END_VAR
  IF IN THEN
    IF et < PT THEN et := et + 1; END_IF;
    Q := (et >= PT);
  ELSE
    et := 0;
    Q := FALSE;
  END_IF;
END_FUNCTION_BLOCK

PROGRAM prog
  VAR Btn : BOOL; Light : BOOL; END_VAR
  VAR T0 : TON_scan; END_VAR
  T0(IN := Btn, PT := 3);
  Light := T0.Q;
END_PROGRAM

CONFIGURATION config
  RESOURCE res ON PLC
    TASK tsk(INTERVAL := T#20ms, PRIORITY := 0);
    PROGRAM inst WITH tsk : prog;
  END_RESOURCE
END_CONFIGURATION
