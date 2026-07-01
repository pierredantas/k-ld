#!/usr/bin/env python3
"""
Rung 6 driver: run every benchmark through K-LD and ESBMC and emit a results table.
For each .ld: pick the frontend (simple <rung> vs graphical netlist), translate,
run the K-LD bounded differential, run ESBMC --ld-props, and record verdicts +
agreement. Writes results.md incrementally so progress is visible.
"""
import os, re, glob, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = "/Users/pierredantas/esbmc/benchmarks"
ESBMC = "/Users/pierredantas/esbmc/build/src/esbmc/esbmc"
GEN = os.path.join(HERE, "gen")
os.makedirs(GEN, exist_ok=True)
OUT = os.path.join(HERE, "results.md")

SKIP_DIRS = {"water_control copy"}
SKIP_FILES = {"beremiz_bacnet.ld"}          # FBD, no <LD>


def props_for(ldpath):
    d = os.path.dirname(ldpath)
    if "unsafe" in os.path.basename(ldpath) and os.path.exists(f"{d}/props_unsafe.yaml"):
        return f"{d}/props_unsafe.yaml"
    for cand in ("props.yaml", "water_control_props.yaml"):
        if os.path.exists(f"{d}/{cand}"):
            return f"{d}/{cand}"
    return None


def run(cmd, timeout, cwd=None):
    # merge stderr into stdout: ESBMC prints its verdict to stderr
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=timeout, cwd=cwd).stdout
    except subprocess.TimeoutExpired:
        return "__TIMEOUT__"


def kld_verdict(name, ldpath, propsf):
    fmt = "simple" if "<rung " in open(ldpath).read() else "graphical"
    frontend = "plcopen2kld.py" if fmt == "simple" else "graphical2kld.py"
    prog = f"{GEN}/{name}.ld"
    side = f"{GEN}/{name}.json"
    with open(prog, "w") as f:
        f.write(run(["python3", f"{HERE}/{frontend}", ldpath, side], 60) or "")
    if "__TIMEOUT__" in open(prog).read() or not os.path.exists(side):
        return fmt, "xlate-fail"
    out = run(["python3", f"{HERE}/differential.py", prog, side, propsf, "3"], 400)
    if out == "__TIMEOUT__":
        return fmt, "timeout"
    viol = re.findall(r'(\w+): VIOLATED', out)
    if viol:
        return fmt, "UNSAFE(" + ",".join(viol) + ")"
    if "SAFE" in out:
        return fmt, "SAFE"
    return fmt, "no-verdict"


def esbmc_verdict(ldpath, propsf):
    out = run([ESBMC, ldpath, "--ld-props", propsf, "--unwind", "6",
               "--no-unwinding-assertions"], 300, cwd=os.path.dirname(ESBMC))
    if out == "__TIMEOUT__":
        return "timeout"
    if "VERIFICATION SUCCESSFUL" in out:
        return "SAFE"
    if "VERIFICATION FAILED" in out:
        return "UNSAFE"
    return "?"


def agree(k, e):
    ks = k.startswith("SAFE")
    ek = e == "SAFE"
    if k in ("timeout", "xlate-fail", "no-verdict") or e in ("timeout", "?"):
        return "-"
    return "yes" if (ks == ek) else "**NO**"


def main():
    lds = sorted(glob.glob(f"{BENCH}/*/*.ld"))
    rows = []
    with open(OUT, "w") as f:
        f.write("# Rung 6 — three-engine results\n\n")
        f.write("| Benchmark | Fmt | K-LD | ESBMC | Agree |\n|---|---|---|---|---|\n")
    for ld in lds:
        d = os.path.basename(os.path.dirname(ld))
        b = os.path.basename(ld)
        if d in SKIP_DIRS or b in SKIP_FILES:
            continue
        name = f"{d}__{b[:-3]}"
        propsf = props_for(ld)
        if not propsf:
            continue
        fmt, k = kld_verdict(name, ld, propsf)
        e = esbmc_verdict(ld, propsf)
        row = f"| {name} | {fmt} | {k} | {e} | {agree(k, e)} |"
        rows.append(row)
        with open(OUT, "a") as f:
            f.write(row + "\n")
        print(row, flush=True)


if __name__ == "__main__":
    main()
