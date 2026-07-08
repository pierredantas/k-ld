#!/usr/bin/env python3
"""
Behavioral trace signature: run a K-ESBMC program on the standard differential input
trace and print a hash of its full per-scan state trace. Two programs with the same
signature are observationally equivalent under the oracle; a mutant whose signature
differs from the original is *behaviorally detected* by the oracle---independent of
whether any benchmark property happens to observe the change. This isolates the
oracle's discriminating power from the benchmarks' (sparse) property suites.

Usage: tracesig.py <prog.ld> <sidecar.json> [sweeps]   ->  prints the trace hash
"""
import sys, re, json, itertools, subprocess, os, hashlib

KLD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    prog, sidecar = sys.argv[1], sys.argv[2]
    sweeps = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    meta = json.load(open(sidecar))
    inputs = meta['inputs']
    state_vars = meta['locals'] + meta['outputs']
    timers = {t['id']: (0, 0, False) for t in meta.get('timers', [])}
    counters = {c['id']: (0, False) for c in meta.get('counters', [])}

    combos = list(itertools.product([False, True], repeat=len(inputs)))
    MAX = 48
    if len(combos) > MAX:
        import random
        random.seed(0)
        combos = [tuple([False]*len(inputs)), tuple([True]*len(inputs))] \
                 + random.sample(combos, MAX-2)
    trace = combos * sweeps
    inlist = " ".join("ListItem(" + " ".join(f"{v} |-> {'true' if b else 'false'}"
                      for v, b in zip(inputs, c)) + ")" for c in trace)
    image0 = {v: False for v in state_vars} | {v: False for v in inputs}
    imap = " ".join(f"{k} |-> {'true' if v else 'false'}" for k, v in image0.items())
    tmap = (".Map" if not timers else " ".join(
        f"{i} |-> tstate({e}, {s}, {'true' if p else 'false'})" for i, (e, s, p) in timers.items()))
    cmap = (".Map" if not counters else " ".join(
        f"{i} |-> cstate({cv}, {'true' if p else 'false'})" for i, (cv, p) in counters.items()))

    prog_rel = os.path.relpath(os.path.abspath(prog), KLD)
    out = subprocess.run(
        ["docker", "run", "--rm", "--platform", "linux/amd64", "-v", f"{KLD}:/work",
         "k-esbmc:latest", "krun", f"/work/{prog_rel}",
         f"-cIMAGE={imap}", f"-cINPUTS={inlist}", f"-cTIMERS={tmap}", "-cDT=1",
         f"-cCOUNTERS={cmap}", "--output", "pretty"],
        capture_output=True, text=True).stdout
    m = re.search(r'<trace>(.*?)</trace>', out, re.S)
    if not m:
        print("NO_TRACE"); return
    # signature over the sequence of images (state vars only, order-normalized)
    sig = []
    for block in re.findall(r'ListItem\s*\((.*?)\)', m.group(1), re.S):
        vals = dict(re.findall(r'(\w+)\s*\|->\s*(true|false)', block))
        sig.append("".join('1' if vals.get(v) == 'true' else '0' for v in sorted(state_vars)))
    print(hashlib.sha1("|".join(sig).encode()).hexdigest()[:16])


if __name__ == '__main__':
    main()
