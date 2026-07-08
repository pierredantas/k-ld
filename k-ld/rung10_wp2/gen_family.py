#!/usr/bin/env python3
"""
WP2 -- controlled synthetic benchmark family for the K-ESBMC differential.

The public suite (13 programs) covers the construct fragment only incidentally --
e.g. its one timer is dead code (paper Sec. 4.4). This generator emits a family
that *systematically* exercises every construct, in both safe and (faithfully)
unsafe variants, with properties that actually OBSERVE the construct under test --
directly addressing the coverage / property-adequacy gap (review W5b, W8).

Each program is emitted in the exact form the differential harness consumes:
  <name>.ld          K-ESBMC DSL (the simple/rung format, per ld-syntax.k)
  <name>.json        { "kinds": { var: input|output|local } }
  <name>.props.yaml  properties (invariant/absence: expression; mutual_exclusion: variables)

It also writes coverage.md -- the programs x constructs x property-kinds matrix
that makes the coverage auditable rather than incidental.

Run:  python3 gen_family.py     # writes into ./family/ and ./coverage.md
Then (when K is available):  for p in family/*.ld; do
        python3 ../rung6/differential.py "$p" "${p%.ld}.json" "${p%.ld}.props.yaml"; done
"""
import os, json

# Construct tags used for the coverage matrix (columns).
TAGS = ["contacts", "XIO", "OR", "latch", "seal-in",
        "TON", "TOF", "TP", "CTU", "CTD", "edge"]

# Each program: name, one-line description, list of DSL rung strings, variable
# classification, properties, expected verdict under a FAITHFUL timer, and the
# construct tags it exercises.
def P(name, desc, ld, inputs, outputs, locals_, props, expected, tags):
    return dict(name=name, desc=desc, ld=ld, inputs=inputs, outputs=outputs,
                locals=locals_, props=props, expected=expected, tags=tags)

# props helpers
def inv(pid, expr):  return dict(id=pid, kind="invariant", expression=expr)
def abse(pid, expr): return dict(id=pid, kind="absence", expression=expr)
def mutex(pid, vs):  return dict(id=pid, kind="mutual_exclusion", variables=vs)

PROGRAMS = [
    # ---- combinational / contacts ------------------------------------------
    P("comb_and", "series contacts (AND) -> coil",
      ["OTE(Y) := XIC(A) * XIC(B) * XIC(C) ;"],
      ["A","B","C"], ["Y"], [],
      [inv("A1", "!Y || (A && B && C)")], "safe", ["contacts"]),

    P("comb_or", "parallel contacts (OR) -> coil",
      ["OTE(Y) := XIC(A) + XIC(B) ;"],
      ["A","B"], ["Y"], [],
      [inv("A1", "!Y || A || B")], "safe", ["contacts","OR"]),

    P("comb_mixed", "series/parallel with a negated (XIO) contact",
      ["OTE(Y) := (XIC(A) * XIO(B)) + XIC(C) ;"],
      ["A","B","C"], ["Y"], [],
      [inv("A1", "!Y || A || C")], "safe", ["contacts","XIO","OR"]),

    # ---- latch / retention -------------------------------------------------
    P("latch_basic", "set/reset latch; unlatch dominant within a scan",
      ["OTL(Q) := XIC(S) ;", "OTU(Q) := XIC(R) ;"],
      ["S","R"], ["Q"], [],
      [abse("A1", "Q && R")], "safe", ["latch"]),

    P("seal_in", "self-holding (seal-in) coil with stop",
      ["OTE(Run) := (XIC(Start) + XIC(Run)) * XIO(Stop) ;"],
      ["Start","Stop"], ["Run"], [],
      [inv("A1", "!Run || !Stop")], "safe", ["contacts","XIO","OR","seal-in"]),

    # ---- timers ------------------------------------------------------------
    P("ton_single", "single on-delay timer (the controlled probe generalised)",
      ["TON(TON0_Q, 3, XIC(Btn)) ;", "OTE(Light) := XIC(TON0_Q) ;"],
      ["Btn"], ["Light"], ["TON0_Q"],
      [inv("A1", "!Light || Btn")], "safe", ["TON"]),

    P("ton_chain2", "chain of two on-delay timers -> mutually exclusive phases",
      ["TON(T1, 2, XIC(Enable)) ;",
       "TON(T2, 2, XIC(T1)) ;",
       "OTE(P1) := XIC(Enable) * XIO(T1) ;",
       "OTE(P2) := XIC(T1) * XIO(T2) ;"],
      ["Enable"], ["P1","P2"], ["T1","T2"],
      [mutex("MX", ["P1","P2"])], "safe", ["TON","XIO"]),

    P("tof_hold", "off-delay holds the light after the sensor clears (stairs-like)",
      ["TOF(TOF0_Q, 5, XIC(Pir)) ;",
       "OTE(Light) := XIC(TOF0_Q) + XIC(Button) ;"],
      ["Pir","Button"], ["Light"], ["TOF0_Q"],
      [inv("P1", "!Light || Pir || Button")], "unsafe", ["TOF","OR"]),

    P("tp_pulse", "pulse timer holds output through the pulse even if input drops",
      ["TP(TP0_Q, 3, XIC(Trig)) ;", "OTE(Out) := XIC(TP0_Q) ;"],
      ["Trig"], ["Out"], ["TP0_Q"],
      [inv("P1", "!Out || Trig")], "unsafe", ["TP"]),

    # ---- counters ----------------------------------------------------------
    P("ctu_saturate", "count-up to preset then saturate; reset dominant",
      ["CTU(CTU0_Q, 2, XIC(Pulse), XIC(Reset)) ;",
       "OTE(Done) := XIC(CTU0_Q) ;"],
      ["Pulse","Reset"], ["Done"], ["CTU0_Q"],
      [abse("A1", "Done && Reset")], "safe", ["CTU"]),

    P("ctd_load", "count-down from preset; load restores the preset",
      ["CTD(CTD0_Q, 2, XIC(Pulse), XIC(Load)) ;",
       "OTE(Empty) := XIC(CTD0_Q) ;"],
      ["Pulse","Load"], ["Empty"], ["CTD0_Q"],
      [abse("A1", "Empty && Load")], "safe", ["CTD"]),

    # ---- edge detection (R_TRIG / F_TRIG via prev-value helper rung) --------
    P("rtrig_edge", "rising-edge one-shot (R_TRIG lowering)",
      ["OTE(Rise) := XIC(Sig) * XIO(Sig_prev) ;",
       "OTE(OneShot) := XIC(Rise) ;",
       "OTE(Sig_prev) := XIC(Sig) ;"],
      ["Sig"], ["OneShot"], ["Rise","Sig_prev"],
      [inv("A1", "!OneShot || Sig")], "safe", ["contacts","XIO","edge"]),

    P("ftrig_edge", "falling-edge one-shot (F_TRIG lowering)",
      ["OTE(Fall) := XIO(Sig) * XIC(Sig_prev) ;",
       "OTE(OneShot) := XIC(Fall) ;",
       "OTE(Sig_prev) := XIC(Sig) ;"],
      ["Sig"], ["OneShot"], ["Fall","Sig_prev"],
      [inv("A1", "!OneShot || !Sig")], "safe", ["contacts","XIO","edge"]),

    # ---- mixed constructs --------------------------------------------------
    P("timer_latch_mix", "timer sets a latched alarm; ack clears it",
      ["TON(T0, 3, XIC(Trig)) ;",
       "OTL(Alarm) := XIC(T0) ;",
       "OTU(Alarm) := XIC(Ack) ;"],
      ["Trig","Ack"], ["Alarm"], ["T0"],
      [abse("A1", "Alarm && Ack")], "safe", ["TON","latch"]),

    P("edge_counter", "rising edges feed a counter; reset dominant",
      ["OTE(Rise) := XIC(Sig) * XIO(Sig_prev) ;",
       "CTU(Cnt_Q, 3, XIC(Rise), XIC(Reset)) ;",
       "OTE(Full) := XIC(Cnt_Q) ;",
       "OTE(Sig_prev) := XIC(Sig) ;"],
      ["Sig","Reset"], ["Full"], ["Rise","Sig_prev","Cnt_Q"],
      [abse("A1", "Full && Reset")], "safe", ["contacts","XIO","edge","CTU"]),
]

def emit_yaml(props):
    out = ["properties:"]
    for p in props:
        out.append(f"  - id: {p['id']}")
        out.append(f"    kind: {p['kind']}")
        if p["kind"] == "mutual_exclusion":
            out.append(f"    variables: [{', '.join(p['variables'])}]")
        else:
            out.append(f"    expression: \"{p['expression']}\"")
    return "\n".join(out) + "\n"

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    fam = os.path.join(here, "family"); os.makedirs(fam, exist_ok=True)
    for pr in PROGRAMS:
        base = os.path.join(fam, pr["name"])
        with open(base + ".ld", "w") as f:
            f.write(f"// {pr['name']}: {pr['desc']}\n")
            f.write("\n".join(pr["ld"]) + "\n")
        kinds = {}
        for v in pr["inputs"]:  kinds[v] = "input"
        for v in pr["outputs"]: kinds[v] = "output"
        for v in pr["locals"]:  kinds[v] = "local"
        with open(base + ".json", "w") as f:
            json.dump({"kinds": kinds}, f, indent=2)
        with open(base + ".props.yaml", "w") as f:
            f.write(emit_yaml(pr["props"]))

    # coverage matrix
    cov = []
    cov.append("# WP2 synthetic family -- construct coverage matrix\n")
    cov.append(f"{len(PROGRAMS)} programs, DSL (simple/rung) format. "
               "✓ = construct exercised. `kinds` lists the property kinds; "
               "`exp.` is the expected verdict under a faithful timer.\n")
    header = "| Program | " + " | ".join(TAGS) + " | kinds | exp. |"
    sep    = "| --- | " + " | ".join("---" for _ in TAGS) + " | --- | --- |"
    cov += [header, sep]
    for pr in PROGRAMS:
        cells = ["✓" if t in pr["tags"] else "" for t in TAGS]
        kinds = ",".join(sorted({p["kind"].split("_")[0] for p in pr["props"]}))
        cov.append(f"| `{pr['name']}` | " + " | ".join(cells) +
                   f" | {kinds} | {pr['expected']} |")
    # column totals
    totals = ["**Σ**"] + [str(sum(1 for pr in PROGRAMS if t in pr["tags"])) for t in TAGS] + ["", ""]
    cov.append("| " + " | ".join(totals) + " |")
    cov.append("")
    n_unsafe = sum(1 for pr in PROGRAMS if pr["expected"] == "unsafe")
    cov.append(f"**Verdict mix:** {len(PROGRAMS)-n_unsafe} safe, {n_unsafe} "
               "unsafe-under-faithful-timer (`tof_hold`, `tp_pulse` -- the timer-hold "
               "cases that a skipping/havocing front-end mishandles).")
    with open(os.path.join(here, "coverage.md"), "w") as f:
        f.write("\n".join(cov) + "\n")

    print(f"wrote {len(PROGRAMS)} programs to family/ (+ coverage.md)")

if __name__ == "__main__":
    main()
