// ============================================================================
//  K-LD :: timer-spec.k  (Rung 8 -- first INDUCTIVE lemma)
//
//  TON done-state stability: once a TON has fired (STATE = 2), holding IN true
//  keeps the done bit true for ANY number of further scans. Unlike the
//  combinational lemmas this is a multi-scan property requiring induction over
//  the input list.
//
//  STATUS: OPEN. The lemma statement below is correct, but kprove does not
//  discharge it out of the box: the scan loop consumes <inputs> by matching
//  `.List` / `ListItem(_) _`, and the prover does not automatically NARROW the
//  symbolic list variable INS into those constructor forms, so the induction
//  never starts (it halts on `<inputs> INS` with allTrue(INS) in the path
//  condition). Closing it needs prover-level help -- an explicit list case-split
//  lemma, or reformulating the scan driver so the loop variable is narrowed --
//  which is left as future work. The combinational + latch lemmas
//  (proof/verification.k) are fully machine-checked.
//
//  Prove (currently does not close):  kprove proof/timer-spec.k --definition ld-haskell
// ============================================================================

requires "../ld-proof.k"

module TIMER-SPEC
  imports LD-PROOF

  // TON done-state stability (inductive over the input list): from the done
  // state tstate(PT,2,true), running ANY input list whose scans all drive IN
  // true keeps the coil `t` true and the timer done. Proved by induction on
  // INS (the loop rule case-splits it; the claim is its own circularity/IH).
  claim <k> #run => .K </k>
        <pgm> TON(t, PT:Int, XIC(inp)) ; </pgm>
        <inputs> INS:List => .List </inputs>
        <image> inp |-> true  t |-> (true => true) </image>
        <trace> _ => ?_:List </trace>
        <timers> t |-> tstate(PT, 2, true) </timers>
        <dt> _DT:Int </dt>
        <counters> .Map </counters>
    requires allTrue(INS) andBool PT >Int 0

endmodule
