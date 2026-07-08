// ============================================================================
//  K-ESBMC  ::  ld-syntax.k
//  Rung 1 -- Abstract syntax for the covered IEC 61131-3 Ladder Diagram fragment.
//  This module fixes the paper's fragment F. Semantics live in ld.k.
// ============================================================================

module LD-SYNTAX
  imports DOMAINS-SYNTAX

  // ---- Rung condition (Boolean network of contacts) ------------------------
  // Series composition (*) = logical AND; parallel composition (+) = logical OR.
  syntax BExp ::= "XIC" "(" Id ")"        // examine-if-closed: bit is TRUE
                | "XIO" "(" Id ")"        // examine-if-open:   bit is FALSE
                | "(" BExp ")"            [bracket]
                > left: BExp "*" BExp     [seqstrict]   // series   (AND)
                > left: BExp "+" BExp     [seqstrict]   // parallel (OR)

  // ---- Output instructions -------------------------------------------------
  syntax Rung ::= "OTE" "(" Id ")" ":=" BExp ";"   // energize while rung true
                | "OTL" "(" Id ")" ":=" BExp ";"   // latch
                | "OTU" "(" Id ")" ":=" BExp ";"   // unlatch

  // ---- Timers (Rung 4) -----------------------------------------------------
  // TIMER(instance, PT, IN): PT is the preset (in time units); IN is the rung
  // condition driving the timer. The done bit Q is exposed in the image under
  // the instance Id, so downstream rungs read it with XIC(instance).
  syntax Rung ::= "TON" "(" Id "," Int "," BExp ")" ";"   // on-delay
                | "TOF" "(" Id "," Int "," BExp ")" ";"   // off-delay
                | "TP"  "(" Id "," Int "," BExp ")" ";"   // pulse

  // ---- Counters (Rung 5) ---------------------------------------------------
  // CTU(inst, PV, CU, R):  count up on rising edge of CU, R resets (dominant).
  // CTD(inst, PV, CD, LD): count down on rising edge of CD, LD loads PV.
  // The done bit Q is exposed in the image under the instance Id (XIC to read).
  syntax Rung ::= "CTU" "(" Id "," Int "," BExp "," BExp ")" ";"
                | "CTD" "(" Id "," Int "," BExp "," BExp ")" ";"

  // A program is a whitespace-separated list of rungs, solved top-to-bottom.
  syntax Pgm ::= List{Rung, ""}

endmodule
