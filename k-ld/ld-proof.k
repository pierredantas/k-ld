// ============================================================================
//  K-LD :: ld-proof.k
//  Proof-harness module: concrete identifier tokens and helper functions used by
//  the kprove specifications (proof/*.k). Kept out of the semantics (ld.k) so the
//  interpreter build is unaffected; kompiled with the Haskell backend for kprove.
// ============================================================================

requires "ld.k"

module LD-PROOF
  imports LD

  // Concrete identifiers, so image-map updates stay decidable for the backend.
  syntax Id ::= "a" [token] | "b" [token] | "q" [token]
              | "inp" [token] | "t" [token]

  // Predicate: every scan in the input list drives `inp` true. Used as a side
  // condition so the loop rule can case-split a genuine list variable while the
  // invariant still knows each consumed input is true.
  syntax Bool ::= allTrue(List) [function, total]
  rule allTrue(.List)                          => true
  rule allTrue(ListItem(inp |-> true) Rest)    => allTrue(Rest)
  rule allTrue(_)                              => false          [owise]

endmodule
