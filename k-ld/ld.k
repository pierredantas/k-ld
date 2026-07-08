// ============================================================================
//  K-ESBMC  ::  ld.k
//  Rung 3 -- scan-cycle model + retentive coils.
//
//  MODEL:
//    <image>  : the persistent bit image (inputs + coils), RETAINED across scans.
//    <inputs> : an input trace -- one Map (input Id |-> Bool) per scan; each scan
//               overlays the next snapshot onto the image before solving.
//    <pgm>    : the pristine program, re-solved every scan.
//    <trace>  : log of the image after each scan (the conformance observable).
//    <k>      : the scan-loop driver.
//
//  One scan = overlay inputs -> solve every rung top-to-bottom against <image>
//  -> log. Coil state that is not rewritten persists, which is what makes OTL/OTU
//  latches (and, in Rung 4+, timers/counters) meaningful.
// ============================================================================

requires "ld-syntax.k"

module LD
  imports LD-SYNTAX
  imports DOMAINS

  configuration
    <k> #run </k>
    <pgm>    $PGM:Pgm    </pgm>
    <image>  $IMAGE:Map  </image>    // Id |-> Bool  (inputs + coils + timer Q), retained
    <inputs> $INPUTS:List </inputs>  // ListItem(Map) per scan
    <trace>  .List       </trace>    // ListItem(Map): image snapshot per scan
    <timers>   $TIMERS:Map   </timers>   // Id |-> tstate(ET, prevIN), retained
    <dt>       $DT:Int       </dt>       // cycle time: time units added to ET per scan
    <counters> $COUNTERS:Map </counters> // Id |-> cstate(CV, prevCount), retained

  // A fully-evaluated rung condition is a Bool; rungs run as K items.
  syntax BExp    ::= Bool
  syntax KResult ::= Bool
  syntax KItem   ::= Rung

  // Per-timer retained state, mirroring the MATIEC reference FB: elapsed time ET,
  // a 3-valued STATE (0 idle, 1 timing, 2 done), and previous IN (edge memory).
  // Elapsed is measured from the trigger edge (ET = 0 on the edge scan), so the
  // timer fires PT/DT scans AFTER the edge -- matching OpenPLC/IEC exactly.
  syntax TState ::= tstate(Int, Int, Bool)   // ET, STATE, prevIN

  // Per-counter retained state: current count, and previous count-input (for
  // rising-edge detection).
  syntax CState ::= cstate(Int, Bool)

  // ---- Scan loop -----------------------------------------------------------
  syntax KItem ::= "#run" | "#endScan"

  // No more input snapshots: halt.
  rule <k> #run => .K ... </k> <inputs> .List </inputs>

  // Next scan: overlay the input snapshot, splice the program, then log & loop.
  rule <k> #run => P ~> #endScan ~> #run ... </k>
       <pgm> P </pgm>
       <inputs> ListItem(In:Map) Rest => Rest </inputs>
       <image> Img => updateMap(Img, In) </image>

  // End of scan: record the image (the observable trace).
  rule <k> #endScan => .K ... </k>
       <image> Img </image>
       <trace> T => T ListItem(Img) </trace>

  // ---- Program sequencing: flatten the rung list into the K sequence --------
  rule <k> R:Rung Rs:Pgm => R ~> Rs ... </k>
  rule <k> .Pgm => .K ... </k>

  // ---- Contact evaluation: read the image ----------------------------------
  rule <k> XIC(X) => B         ... </k> <image> ... X |-> B ... </image>
  rule <k> XIO(X) => notBool B ... </k> <image> ... X |-> B ... </image>

  // ---- Series (AND) and parallel (OR) -- strictness declared in LD-SYNTAX ---
  rule B1:Bool * B2:Bool => B1 andBool B2
  rule B1:Bool + B2:Bool => B1 orBool B2

  // ---- OTE: unconditional -- coil follows the rung condition ----------------
  syntax KItem ::= "#write" "(" Id ")"
  rule <k> OTE(C) := E ; => E ~> #write(C) ... </k>
  rule <k> B:Bool ~> #write(C) => .K ... </k>
       <image> Img => Img [ C <- B ] </image>

  // ---- OTL (latch/set): rung true sets the coil; false RETAINS it -----------
  syntax KItem ::= "#latch" "(" Id ")"
  rule <k> OTL(C) := E ; => E ~> #latch(C) ... </k>
  rule <k> true  ~> #latch(C) => .K ... </k>
       <image> Img => Img [ C <- true ] </image>
  rule <k> false ~> #latch(_) => .K ... </k>                 // retain: no write

  // ---- OTU (unlatch/reset): rung true resets the coil; false RETAINS it ------
  syntax KItem ::= "#unlatch" "(" Id ")"
  rule <k> OTU(C) := E ; => E ~> #unlatch(C) ... </k>
  rule <k> true  ~> #unlatch(C) => .K ... </k>
       <image> Img => Img [ C <- false ] </image>
  rule <k> false ~> #unlatch(_) => .K ... </k>               // retain: no write

  // ============================================================================
  //  Timers -- direct port of the MATIEC/OpenPLC reference FBs (iec_std_FB.h).
  //  STATE: 0 idle, 1 timing, 2 done. Elapsed ET measured from the trigger edge
  //  (ET = 0 on the edge scan); fires when ET reaches PT, i.e. PT/DT scans after
  //  the edge -- so K-ESBMC agrees with OpenPLC scan-for-scan.
  // ============================================================================

  // ---- TON (on-delay) ------------------------------------------------------
  syntax KItem ::= "#ton" "(" Id "," Int ")"
  rule <k> TON(T, PT, E) ; => E ~> #ton(T, PT) ... </k>

  // IN false: reset (any STATE) -> idle, Q false.
  rule <k> false ~> #ton(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ => 0, _ => 0, _ => false) ... </timers>
       <image> Img => Img [ T <- false ] </image>

  // Rising edge (STATE 0, prevIN false): begin timing, elapsed 0, Q false.
  rule <k> true ~> #ton(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ => 0, 0 => 1, false => true) ... </timers>
       <image> Img => Img [ T <- false ] </image>

  // Timing (STATE 1), not yet reached PT: accumulate, Q false.
  rule <k> true ~> #ton(T, PT) => .K ... </k>
       <dt> DT </dt>
       <timers> ... T |-> tstate(ET => ET +Int DT, 1 => 1, _ => true) ... </timers>
       <image> Img => Img [ T <- false ] </image>
    requires ET +Int DT <Int PT

  // Timing (STATE 1), reaches PT: fire -> done, ET := PT, Q true.
  rule <k> true ~> #ton(T, PT) => .K ... </k>
       <dt> DT </dt>
       <timers> ... T |-> tstate(ET => PT, 1 => 2, _ => true) ... </timers>
       <image> Img => Img [ T <- true ] </image>
    requires ET +Int DT >=Int PT

  // Done (STATE 2), IN held true: hold Q true.
  rule <k> true ~> #ton(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ET, 2 => 2, _ => true) ... </timers>
       <image> Img => Img [ T <- true ] </image>

  // ---- TOF (off-delay): Q := IN OR (still counting) ------------------------
  syntax KItem ::= "#tof" "(" Id "," Int ")"
  rule <k> TOF(T, PT, E) ; => E ~> #tof(T, PT) ... </k>

  // IN true: pass through -> idle, ET 0, Q true.
  rule <k> true ~> #tof(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ => 0, _ => 0, _ => true) ... </timers>
       <image> Img => Img [ T <- true ] </image>

  // Falling edge (STATE 0, prevIN true): begin countdown, elapsed 0, Q still true.
  rule <k> false ~> #tof(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ => 0, 0 => 1, true => false) ... </timers>
       <image> Img => Img [ T <- true ] </image>

  // Counting (STATE 1), not yet reached PT: accumulate, Q true.
  rule <k> false ~> #tof(T, PT) => .K ... </k>
       <dt> DT </dt>
       <timers> ... T |-> tstate(ET => ET +Int DT, 1 => 1, _ => false) ... </timers>
       <image> Img => Img [ T <- true ] </image>
    requires ET +Int DT <Int PT

  // Counting (STATE 1), reaches PT: expire -> done, Q false.
  rule <k> false ~> #tof(T, PT) => .K ... </k>
       <dt> DT </dt>
       <timers> ... T |-> tstate(ET => PT, 1 => 2, _ => false) ... </timers>
       <image> Img => Img [ T <- false ] </image>
    requires ET +Int DT >=Int PT

  // Idle-off (STATE 0, prevIN false) or done-off (STATE 2), IN false: Q false.
  rule <k> false ~> #tof(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ET, 0 => 0, false => false) ... </timers>
       <image> Img => Img [ T <- false ] </image>
  rule <k> false ~> #tof(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ET, 2 => 2, _ => false) ... </timers>
       <image> Img => Img [ T <- false ] </image>

  // ---- TP (pulse) ----------------------------------------------------------
  syntax KItem ::= "#tp" "(" Id "," Int ")"
  rule <k> TP(T, PT, E) ; => E ~> #tp(T, PT) ... </k>

  // Rising edge (STATE 0, prevIN false, IN true): start pulse, Q true, ET 0.
  rule <k> true ~> #tp(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ => 0, 0 => 1, false => true) ... </timers>
       <image> Img => Img [ T <- true ] </image>

  // Pulsing (STATE 1), not yet reached PT: accumulate, Q true, IN ignored.
  rule <k> IN:Bool ~> #tp(T, PT) => .K ... </k>
       <dt> DT </dt>
       <timers> ... T |-> tstate(ET => ET +Int DT, 1 => 1, _ => IN) ... </timers>
       <image> Img => Img [ T <- true ] </image>
    requires ET +Int DT <Int PT

  // Pulse completes with IN true: -> done-wait (STATE 2), Q false.
  rule <k> true ~> #tp(T, PT) => .K ... </k>
       <dt> DT </dt>
       <timers> ... T |-> tstate(ET => PT, 1 => 2, _ => true) ... </timers>
       <image> Img => Img [ T <- false ] </image>
    requires ET +Int DT >=Int PT

  // Pulse completes with IN false: re-arm immediately (MATIEC resets STATE 2->0
  // in the same scan when IN is low), Q false.
  rule <k> false ~> #tp(T, PT) => .K ... </k>
       <dt> DT </dt>
       <timers> ... T |-> tstate(ET => 0, 1 => 0, _ => false) ... </timers>
       <image> Img => Img [ T <- false ] </image>
    requires ET +Int DT >=Int PT

  // Done-wait (STATE 2), IN false: re-arm to idle, Q false.
  rule <k> false ~> #tp(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ => 0, 2 => 0, _ => false) ... </timers>
       <image> Img => Img [ T <- false ] </image>

  // Done-wait (STATE 2), IN held true: stay off.
  rule <k> true ~> #tp(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ET, 2 => 2, _ => true) ... </timers>
       <image> Img => Img [ T <- false ] </image>

  // Idle (STATE 0), IN false (no edge): stay off.
  rule <k> false ~> #tp(T, _PT) => .K ... </k>
       <timers> ... T |-> tstate(_ET, 0 => 0, _ => false) ... </timers>
       <image> Img => Img [ T <- false ] </image>

  // ---- CTU (count up): rising edge of CU increments CV; R resets (dominant);
  //      Q := CV >= PV. Evaluate CU then R, then apply. -----------------------
  syntax KItem ::= "#ctuR" "(" Id "," Int "," BExp ")"     // CU done; evaluate R next
                 | "#ctu"  "(" Id "," Int "," Bool ")"     // both known: R on top, CU carried
  rule <k> CTU(I, PV, CU, R) ; => CU ~> #ctuR(I, PV, R) ... </k>
  rule <k> CUv:Bool ~> #ctuR(I, PV, R) => R ~> #ctu(I, PV, CUv) ... </k>

  // R true: reset dominates -- CV := 0, record CU as prev, Q := (0 >= PV).
  rule <k> true ~> #ctu(I, PV, CUv) => .K ... </k>
       <counters> ... I |-> cstate(_ => 0, _ => CUv) ... </counters>
       <image> Img => Img [ I <- (0 >=Int PV) ] </image>

  // R false, rising edge of CU (prev false), below preset: increment (CV caps at
  // PV -- MATIEC guards the increment with CV < PV).
  rule <k> false ~> #ctu(I, PV, true) => .K ... </k>
       <counters> ... I |-> cstate(CV => CV +Int 1, false => true) ... </counters>
       <image> Img => Img [ I <- (CV +Int 1 >=Int PV) ] </image>
    requires CV <Int PV

  // R false, rising edge but already at/above preset: hold CV (saturated).
  rule <k> false ~> #ctu(I, PV, true) => .K ... </k>
       <counters> ... I |-> cstate(CV, false => true) ... </counters>
       <image> Img => Img [ I <- (CV >=Int PV) ] </image>
    requires CV >=Int PV

  // R false, CU held high (prev true): no edge, hold.
  rule <k> false ~> #ctu(I, PV, true) => .K ... </k>
       <counters> ... I |-> cstate(CV, true => true) ... </counters>
       <image> Img => Img [ I <- (CV >=Int PV) ] </image>

  // R false, CU low: hold, clear edge memory.
  rule <k> false ~> #ctu(I, PV, false) => .K ... </k>
       <counters> ... I |-> cstate(CV, _ => false) ... </counters>
       <image> Img => Img [ I <- (CV >=Int PV) ] </image>

  // ---- CTD (count down): rising edge of CD decrements CV (floor 0); LD loads
  //      PV (dominant); Q := CV <= 0. --------------------------------------------
  syntax KItem ::= "#ctdL" "(" Id "," Int "," BExp ")"     // CD done; evaluate LD next
                 | "#ctd"  "(" Id "," Int "," Bool ")"     // both known: LD on top, CD carried
  rule <k> CTD(I, PV, CD, LDe) ; => CD ~> #ctdL(I, PV, LDe) ... </k>
  rule <k> CDv:Bool ~> #ctdL(I, PV, LDe) => LDe ~> #ctd(I, PV, CDv) ... </k>

  // LD true: load dominates -- CV := PV, record CD as prev, Q := (PV <= 0).
  rule <k> true ~> #ctd(I, PV, CDv) => .K ... </k>
       <counters> ... I |-> cstate(_ => PV, _ => CDv) ... </counters>
       <image> Img => Img [ I <- (PV <=Int 0) ] </image>

  // LD false, rising edge of CD (prev false): decrement, floored at 0.
  rule <k> false ~> #ctd(I, _PV, true) => .K ... </k>
       <counters> ... I |-> cstate(CV => maxInt(CV -Int 1, 0), false => true) ... </counters>
       <image> Img => Img [ I <- (maxInt(CV -Int 1, 0) <=Int 0) ] </image>

  // LD false, CD held high (prev true): no edge, hold.
  rule <k> false ~> #ctd(I, _PV, true) => .K ... </k>
       <counters> ... I |-> cstate(CV, true => true) ... </counters>
       <image> Img => Img [ I <- (CV <=Int 0) ] </image>

  // LD false, CD low: hold, clear edge memory.
  rule <k> false ~> #ctd(I, _PV, false) => .K ... </k>
       <counters> ... I |-> cstate(CV, _ => false) ... </counters>
       <image> Img => Img [ I <- (CV <=Int 0) ] </image>

endmodule
