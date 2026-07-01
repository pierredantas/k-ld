#!/usr/bin/env python3
"""
Rung 6 / E3 differential oracle -- K-LD side (trace-based, timers-aware).

krun startup is ~30 s under emulation, so per-transition BFS is infeasible. Instead
we pay startup ONCE: drive K-LD with a single long input trace that cycles through
every input combination over several sweeps (letting timers/latches evolve), and
check each props.yaml invariant on every per-scan image K-LD logs in <trace>.

This is a BOUNDED differential -- it fairly matches ESBMC's bounded unwinding. A
property is VIOLATED if some scan's image falsifies it (with that scan as witness),
else reported SAFE-up-to-bound.

Usage: differential.py <prog.ld> <sidecar.json> <props.yaml> [sweeps]
"""
import sys, re, json, itertools, subprocess, os

IMG = os.path.dirname(os.path.abspath(__file__))
KLD = os.path.dirname(IMG)


def load_props(path):
    """Return (id, kind, expr). kind 'absence' means expr is a BAD condition that
    must never hold; otherwise expr is an invariant that must always hold.
    mutual_exclusion([A,B,..]) is synthesised as absence of any pair both true."""
    import itertools as _it
    props = []
    pid = kind = None
    for line in open(path):
        m = re.search(r'id:\s*(\S+)', line)
        if m:
            pid, kind = m.group(1), 'invariant'
        mk = re.search(r'kind:\s*(\S+)', line)
        if mk:
            kind = mk.group(1)
        mv = re.search(r'variables:\s*\[(.*?)\]', line)
        if mv and pid and kind == 'mutual_exclusion':
            vs = [v.strip() for v in mv.group(1).split(',') if v.strip()]
            bad = " || ".join(f"({a} && {b})" for a, b in _it.combinations(vs, 2))
            props.append((pid, 'absence', bad))
            pid = None
        mex = re.search(r'expression:\s*"(.*)"', line)
        if mex and pid:
            props.append((pid, kind, mex.group(1)))
            pid = None
    return props


def prop_holds(kind, expr, image):
    """True iff the property is satisfied in this image."""
    v = eval_prop(expr, image)
    return (not v) if kind == 'absence' else v


def eval_prop(expr, image):
    py = expr.replace('||', ' or ').replace('&&', ' and ').replace('!', ' not ')
    return bool(eval(py, {"__builtins__": {}}, {k: bool(v) for k, v in image.items()}))


def main():
    prog, sidecar, propsf = sys.argv[1], sys.argv[2], sys.argv[3]
    sweeps = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    meta = json.load(open(sidecar))
    inputs = meta['inputs']
    state_vars = meta['locals'] + meta['outputs']
    timers = {t['id']: (0, 0, False) for t in meta.get('timers', [])}
    counters = {c['id']: (0, False) for c in meta.get('counters', [])}
    props = load_props(propsf)

    # Input trace: every combination (or a bounded random sample when the input
    # space is large), repeated over `sweeps` passes.
    MAX_COMBOS = 48
    allc = list(itertools.product([False, True], repeat=len(inputs)))
    if len(allc) > MAX_COMBOS:
        import random
        random.seed(0)
        combos = [tuple([False] * len(inputs)), tuple([True] * len(inputs))]
        combos += random.sample(allc, MAX_COMBOS - 2)
    else:
        combos = allc
    trace = combos * sweeps
    inlist = " ".join(
        "ListItem(" + " ".join(f"{v} |-> {'true' if b else 'false'}"
                               for v, b in zip(inputs, combo)) + ")"
        for combo in trace)

    image0 = {v: False for v in state_vars} | {v: False for v in inputs}
    imap = " ".join(f"{k} |-> {'true' if v else 'false'}" for k, v in image0.items())
    tmap = (".Map" if not timers else
            " ".join(f"{i} |-> tstate({e}, {s}, {'true' if p else 'false'})"
                     for i, (e, s, p) in timers.items()))
    cmap = (".Map" if not counters else
            " ".join(f"{i} |-> cstate({cv}, {'true' if p else 'false'})"
                     for i, (cv, p) in counters.items()))

    prog_rel = os.path.relpath(os.path.abspath(prog), KLD)   # e.g. rung6/gen/foo.ld
    cmd = ["docker", "run", "--rm", "--platform", "linux/amd64",
           "-v", f"{KLD}:/work", "k-ld:latest", "krun", f"/work/{prog_rel}",
           f"-cIMAGE={imap}", f"-cINPUTS={inlist}", f"-cTIMERS={tmap}",
           "-cDT=1", f"-cCOUNTERS={cmap}", "--output", "pretty"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout

    # Parse the <trace> cell: one ListItem(<image map>) per scan.
    mt = re.search(r'<trace>(.*?)</trace>', out, re.S)
    if not mt:
        sys.stderr.write("no <trace> in krun output:\n" + out[:600] + "\n")
        sys.exit(1)
    images = []
    for block in re.findall(r'ListItem\s*\((.*?)\)', mt.group(1), re.S):
        images.append({k: (v == 'true')
                       for k, v in re.findall(r'(\w+)\s*\|->\s*(true|false)', block)})

    violations = {pid: None for pid, _, _ in props}
    for idx, img in enumerate(images):
        for pid, kind, expr in props:
            if violations[pid] is None and not prop_holds(kind, expr, img):
                violations[pid] = (idx, img)

    print(f"# K-LD bounded differential: {len(images)} scans "
          f"({len(combos)} input combos x {sweeps} sweeps)\n")
    for pid, kind, expr in props:
        w = violations[pid]
        if w is None:
            print(f"{pid}: SAFE-up-to-bound  [{kind}: {expr}]")
        else:
            idx, img = w
            wt = ", ".join(f"{k}={'T' if v else 'F'}" for k, v in sorted(img.items())
                           if k in expr)
            print(f"{pid}: VIOLATED @scan{idx}  [{kind}: {expr}]  {wt}")


if __name__ == '__main__':
    main()
