// ============================================================================
//  K-LD :: verification.k  (Rung 8 -- machine-checked construct lemmas)
//
//  Reachability claims proved with `kprove` against the K-LD semantics. Each
//  lemma states the IEC 61131-3 input/output relation for one construct,
//  discharged symbolically over the bit values (VA, VB). Concrete identifiers
//  (#token) keep the image-map updates decidable for the Haskell backend.
//  Composed on paper into the whole-program correspondence, these ground K-LD
//  as a reference oracle.
//
//  Build:  kompile --backend haskell ld.k   (proof Makefile target `prove-build`)
//  Prove:  kprove proof/verification.k --definition ld-haskell   (`prove`)
// ============================================================================

requires "../ld-proof.k"

module VERIFICATION
  imports LD-PROOF

  // ---- L1 (series contacts = AND): coil := bit(a) AND bit(b) ---------------
  claim <k> OTE(q) := XIC(a) * XIC(b) ; => .K ... </k>
        <image> a |-> VA:Bool  b |-> VB:Bool  q |-> (_V:Bool => (VA andBool VB)) </image>

  // ---- L2 (parallel contacts = OR): coil := bit(a) OR bit(b) ----------------
  claim <k> OTE(q) := XIC(a) + XIC(b) ; => .K ... </k>
        <image> a |-> VA:Bool  b |-> VB:Bool  q |-> (_V:Bool => (VA orBool VB)) </image>

  // ---- L3 (XIO = negated contact): coil := NOT bit(a) -----------------------
  claim <k> OTE(q) := XIO(a) ; => .K ... </k>
        <image> a |-> VA:Bool  q |-> (_V:Bool => (notBool VA)) </image>

  // ---- L4 (OTL sets on a true rung) ----------------------------------------
  claim <k> OTL(q) := XIC(a) ; => .K ... </k>
        <image> a |-> true  q |-> (_V:Bool => true) </image>

  // ---- L5 (OTL RETAINS on a false rung) ------------------------------------
  claim <k> OTL(q) := XIC(a) ; => .K ... </k>
        <image> a |-> false  q |-> (VQ:Bool => VQ) </image>

  // ---- L6 (OTU resets on a true rung) --------------------------------------
  claim <k> OTU(q) := XIC(a) ; => .K ... </k>
        <image> a |-> true  q |-> (_V:Bool => false) </image>

  // ---- L7 (OTU RETAINS on a false rung) ------------------------------------
  claim <k> OTU(q) := XIC(a) ; => .K ... </k>
        <image> a |-> false  q |-> (VQ:Bool => VQ) </image>

endmodule
