#!/usr/bin/env python3
"""
WP3 fault-injection campaign over the WP2 synthetic family.

Reuses rung7's five translation-fault operators (CP/CO/LR/GC/TK), but runs them
over the latch- and timer-heavy WP2 family so that LR (latch-retention drop) and
TK (timer-kind swap) -- inert in the original tank+bottle study -- fire abundantly.

For each single-point mutant we classify, using the validated ld_exec oracle:
  * behavioral   -- the per-scan trace differs from the original (observable fault)
  * property     -- the benchmark's own property verdict/violated-set changes
The gap between them is the property-adequacy finding (review W8): the oracle sees
every observable fault, but a property-based verifier catches one only when a
property happens to constrain the affected variable.

Writes RESULTS.md. Run: python3 mutate_campaign.py
"""
import os, sys, glob, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ld_exec, wp3lib

# import rung7's mutation operators
spec = importlib.util.spec_from_file_location("mutate", os.path.join(HERE, "..", "rung7", "mutate.py"))
mutate = importlib.util.module_from_spec(spec); spec.loader.exec_module(mutate)
OPS = mutate.OPS
OP_NAME = {"CP": "contact-polarity", "CO": "coil-op OTE->OTL", "LR": "latch-retention drop",
           "GC": "guard-contact drop", "TK": "timer-kind TON<->TOF"}

FAM = os.path.join(HERE, "..", "rung10_wp2", "family")

def signature(imgs):
    return tuple(tuple(sorted(img.items())) for img in imgs)

def mutants(ld_text):
    lines = ld_text.splitlines()
    for op, fn in OPS.items():
        for i, line in enumerate(lines):
            for mut in fn(line):
                if mut == line:
                    continue
                yield op, "\n".join(lines[:i] + [mut] + lines[i+1:])

def main():
    # per-operator tallies: [mutants, behavioral, property, invalid]
    tally = {op: [0, 0, 0, 0] for op in OPS}
    rows = []
    for ld in sorted(glob.glob(os.path.join(FAM, "*.ld"))):
        name = os.path.basename(ld)[:-3]
        text = open(ld).read()
        kinds = wp3lib.load_kinds(ld[:-3] + ".json")
        props = wp3lib.load_props(ld[:-3] + ".props.yaml")
        inputs = [v for v, k in kinds.items() if k == "input"]
        trace = wp3lib.make_trace(inputs)
        base_imgs = ld_exec.run(text, trace)
        base_sig = signature(base_imgs)
        base_ver = wp3lib.evaluate(base_imgs, props)
        pm = pb = pp = 0
        for op, mtext in mutants(text):
            tally[op][0] += 1; pm += 1
            try:
                imgs = ld_exec.run(mtext, trace)
            except Exception:
                tally[op][3] += 1; continue   # unparseable mutant
            beh = signature(imgs) != base_sig
            pro = wp3lib.evaluate(imgs, props) != base_ver
            if beh: tally[op][1] += 1; pb += 1
            if pro: tally[op][2] += 1; pp += 1
        rows.append((name, pm, pb, pp))

    # ---- render RESULTS.md --------------------------------------------------
    tot = [sum(tally[op][j] for op in OPS) for j in range(4)]
    out = []
    out.append("# WP3 — fault-injection campaign over the WP2 family\n")
    out.append("Five translation-fault operators (rung7) over the 15-program WP2 family, "
               "classified with the validated `ld_exec` oracle (`validate_exec.py`: it "
               "reproduces the RQ1 reference traces and all WP2 labels).\n")
    out.append("## Per-operator detection\n")
    out.append("| Op | Fault class | Mutants | Behavioral | Property | Beh% | Prop%(of beh) |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    for op in OPS:
        m, b, p, inv = tally[op]
        beh = f"{100*b/m:.0f}%" if m else "-"
        pob = f"{100*p/b:.0f}%" if b else "-"
        out.append(f"| {op} | {OP_NAME[op]} | {m} | {b} | {p} | {beh} | {pob} |")
    out.append(f"| **Σ** | | **{tot[0]}** | **{tot[1]}** | **{tot[2]}** | "
               f"**{100*tot[1]/tot[0]:.0f}%** | **{100*tot[2]/tot[1]:.0f}%** |")
    out.append("")
    out.append(f"**Property-adequacy gap:** of {tot[1]} behavior-changing mutants the "
               f"benchmark properties detect only {tot[2]} "
               f"(**{100*tot[2]/tot[1]:.0f}%**) -- the oracle sees every observable fault; "
               "a property catches one only when it constrains the affected variable.\n")
    out.append("## The previously-inert operators now fire\n")
    lr, tk = tally["LR"], tally["TK"]
    out.append(f"In the original tank+bottle study (rung7) **LR fired 0 times and TK once** "
               f"(on dead code). Over the WP2 family **LR fires {lr[0]} times "
               f"and TK {tk[0]} times**, exercising latch-retention and timer-kind faults "
               "that the public suite could not.\n")
    out.append("## Per-program\n")
    out.append("| Program | Mutants | Behavioral | Property |")
    out.append("| --- | --- | --- | --- |")
    for name, m, b, p in rows:
        out.append(f"| `{name}` | {m} | {b} | {p} |")
    out.append("")
    out.append("_Oracle: validated `ld_exec` (krun unavailable in this environment); the "
               "canonical run is `rung6/differential.py` under K._")
    with open(os.path.join(HERE, "RESULTS.md"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))

if __name__ == "__main__":
    main()
