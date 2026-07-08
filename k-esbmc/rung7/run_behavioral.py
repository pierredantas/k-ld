#!/usr/bin/env python3
"""
Behavioral (trace-level) mutation detection: for each mutant in mut_<name>/, compare
its trace signature (tracesig.py) to the original's. A mutant is BEHAVIORALLY KILLED
iff its signature differs---i.e., the oracle produces a distinguishable execution.
Survivors here are observationally equivalent mutants (the fault has no effect on any
scan of any variable), the theoretical ceiling on any oracle. This measures the
oracle's discriminating power, separate from benchmark property coverage.

Usage: run_behavioral.py <name> <original.ld> <sidecar.json> [sweeps]
"""
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def sig(prog, sidecar, sweeps):
    return subprocess.run(['python3', os.path.join(HERE, 'tracesig.py'), prog, sidecar, str(sweeps)],
                          capture_output=True, text=True).stdout.strip()


def main():
    name, orig, sidecar = sys.argv[1:4]
    sweeps = sys.argv[4] if len(sys.argv) > 4 else '3'
    base = sig(orig, sidecar, sweeps)
    print(f'[{name}] baseline sig = {base}', flush=True)
    outdir = os.path.join(HERE, f'mut_{name}')
    mutants = sorted(f for f in os.listdir(outdir) if f.endswith('.ld'))
    tally, survivors = {}, []
    for i, mf in enumerate(mutants):
        op = mf.split('_')[0]; tally.setdefault(op, [0, 0]); tally[op][1] += 1
        s = sig(os.path.join(outdir, mf), sidecar, sweeps)
        killed = (s != base) and s != 'NO_TRACE' or s == 'NO_TRACE'
        if killed: tally[op][0] += 1
        else: survivors.append(mf[:-3])
        print(f'  [{i+1}/{len(mutants)}] {mf[:-3]:8} {"KILLED" if killed else "equiv"}', flush=True)
    lines = [f'# E4 behavioral (trace-level) detection -- {name}\n',
             '| Operator | Killed | Total | Detection |', '|---|---|---|---|']
    labels = {'CP': 'contact polarity', 'CO': 'coil-op', 'LR': 'latch-drop',
              'GC': 'guard drop', 'TK': 'timer-kind swap'}
    tk = tt = 0
    for op in ('CP', 'CO', 'LR', 'GC', 'TK'):
        if op in tally:
            k, t = tally[op]; tk += k; tt += t
            lines.append(f'| {op} ({labels[op]}) | {k} | {t} | {100*k//t}% |')
    lines.append(f'| **overall** | **{tk}** | **{tt}** | **{100*tk//tt if tt else 0}%** |')
    if survivors:
        lines.append(f'\nEquivalent mutants (no trace change): {", ".join(survivors)}')
    rep = '\n'.join(lines) + '\n'
    open(os.path.join(HERE, f'behav_{name}.md'), 'w').write(rep)
    print('\n' + rep)


if __name__ == '__main__':
    main()
