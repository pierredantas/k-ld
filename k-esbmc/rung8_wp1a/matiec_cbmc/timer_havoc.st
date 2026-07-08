(* Havoc timer: output Q is left unconstrained via an external read (the ESBMC
   'simple format' defect). MATIEC compiles the read of an un-driven input Q_ext,
   which CBMC treats as nondeterministic -> manufactures the false alarm. *)
FUNCTION_BLOCK TON_havoc
  VAR_INPUT IN : BOOL; PT : INT; Q_ext : BOOL; END_VAR
  VAR_OUTPUT Q : BOOL; END_VAR
  Q := Q_ext;
END_FUNCTION_BLOCK
PROGRAM prog
  VAR Btn : BOOL; Light : BOOL; Free : BOOL; END_VAR
  VAR T0 : TON_havoc; END_VAR
  T0(IN := Btn, PT := 3, Q_ext := Free);
  Light := T0.Q;
END_PROGRAM
CONFIGURATION config
  RESOURCE res ON PLC
    TASK tsk(INTERVAL := T#20ms, PRIORITY := 0);
    PROGRAM inst WITH tsk : prog;
  END_RESOURCE
END_CONFIGURATION
