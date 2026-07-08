#!/usr/bin/env python3
"""Validate ld_exec against (1) the paper's RQ1 reference done-bit traces
(Table 2 / MATIEC ground truth) and (2) the WP2 family's expected verdict labels.
If both pass, the executor is trustworthy as the WP3 measurement instrument."""
import os, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ld_exec, wp3lib

FAM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rung10_wp2", "family")

# ---- (1) RQ1 reference traces (from validation/matiec_ref.c input sequences) --
def bits(s): return [c == "1" for c in s]
RQ1 = [
    ("TON(T0, 3, XIC(I0)) ;",              {"I0": "11110"},               "T0", "FFFTF"),
    ("TOF(T0, 3, XIC(I0)) ;",              {"I0": "110000"},              "T0", "TTTTTF"),
    ("TP(T0, 3, XIC(I0)) ;",               {"I0": "011101"},              "T0", "FTTTFT"),
    ("CTU(C0, 2, XIC(I0), XIC(I1)) ;",     {"I0": "0110110", "I1": "0000010"}, "C0", "FFFFTFF"),
    ("CTD(C0, 2, XIC(I0), XIC(I1)) ;",     {"I0": "0110110", "I1": "1000001"}, "C0", "FFFFTTF"),
]

def check_rq1():
    ok = True
    for prog, ins, out, expected in RQ1:
        n = len(expected)
        trace = [{v: bits(seq)[i] for v, seq in ins.items()} for i in range(n)]
        imgs = ld_exec.run(prog, trace)
        got = "".join("T" if img[out] else "F" for img in imgs)
        mark = "ok" if got == expected else "MISMATCH"
        if got != expected: ok = False
        print(f"  {prog.split('(')[0]:5s} got={got}  expected={expected}  {mark}")
    return ok

# ---- (2) WP2 family expected labels -----------------------------------------
# expected verdicts come from the generator spec (mirrored here)
EXPECTED = {
    "comb_and":"safe","comb_or":"safe","comb_mixed":"safe","latch_basic":"safe",
    "seal_in":"safe","ton_single":"safe","ton_chain2":"safe","tof_hold":"unsafe",
    "tp_pulse":"unsafe","ctu_saturate":"safe","ctd_load":"safe","rtrig_edge":"safe",
    "ftrig_edge":"safe","timer_latch_mix":"safe","edge_counter":"safe",
}

def check_family():
    ok = True
    for ld in sorted(glob.glob(os.path.join(FAM, "*.ld"))):
        name = os.path.basename(ld)[:-3]
        kinds = wp3lib.load_kinds(ld[:-3] + ".json")
        props = wp3lib.load_props(ld[:-3] + ".props.yaml")
        inputs = [v for v, k in kinds.items() if k == "input"]
        imgs = ld_exec.run(open(ld).read(), wp3lib.make_trace(inputs))
        verdict, _ = wp3lib.evaluate(imgs, props)
        exp = EXPECTED.get(name, "?")
        mark = "ok" if verdict == exp else "MISMATCH"
        if verdict != exp: ok = False
        print(f"  {name:16s} verdict={verdict:6s} expected={exp:6s} {mark}")
    return ok

if __name__ == "__main__":
    print("== (1) RQ1 reference done-bit traces ==")
    a = check_rq1()
    print("== (2) WP2 family expected labels ==")
    b = check_family()
    print(f"\nRESULT: RQ1 {'PASS' if a else 'FAIL'}, family {'PASS' if b else 'FAIL'}")
    sys.exit(0 if a and b else 1)
