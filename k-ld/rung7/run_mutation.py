#!/usr/bin/env python3
"""
E4 mutation driver. For one benchmark:
  1. run the K-ESBMC differential on the original program -> baseline verdict vector
     (per property: S = safe-to-bound, V = violated);
  2. generate all single-point mutants (mutate.py);
  3. run the differential on each mutant; a mutant is KILLED iff its verdict vector
     differs from the baseline on any property (the oracle detects the fault);
  4. report kill rate overall and per operator.

Usage: run_mutation.py <name> <prog.ld> <sidecar.json> <props.yaml> [sweeps]
Writes results to results_<name>.md; prints progress.
"""
import sys, re, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RUNG6 = os.path.join(os.path.dirname(HERE), 'rung6')


def verdict_vector(prog, sidecar, props, sweeps):
    """Run the differential; return {pid: 'S'|'V'} or None on failure."""
    out = subprocess.run(
        ['python3', os.path.join(RUNG6, 'differential.py'), prog, sidecar, props, str(sweeps)],
        capture_output=True, text=True).stdout
    vec = {}
    for pid, verd in re.findall(r'(\w+):\s+(SAFE|VIOLATED)', out):
        vec[pid] = 'V' if verd == 'VIOLATED' else 'S'
    return vec or None


def main():
    name, prog, sidecar, props = sys.argv[1:5]
    sweeps = sys.argv[5] if len(sys.argv) > 5 else '3'

    print(f'[{name}] baseline ...', flush=True)
    base = verdict_vector(prog, sidecar, props, sweeps)
    if not base:
        print('  baseline FAILED (no verdict)'); return
    print(f'  baseline = {base}', flush=True)

    outdir = os.path.join(HERE, f'mut_{name}')
    subprocess.run(['python3', os.path.join(HERE, 'mutate.py'), prog, outdir],
                   capture_output=True, text=True)
    mutants = sorted(f for f in os.listdir(outdir) if f.endswith('.ld'))

    tally = {}   # op -> [killed, total]
    survivors = []
    for i, mf in enumerate(mutants):
        op = mf.split('_')[0]
        tally.setdefault(op, [0, 0])
        tally[op][1] += 1
        v = verdict_vector(os.path.join(outdir, mf), sidecar, props, sweeps)
        killed = (v is None) or (v != base)   # crash or verdict change = detected
        if killed:
            tally[op][0] += 1
        else:
            survivors.append(mf[:-3])
        print(f'  [{i+1}/{len(mutants)}] {mf[:-3]:8} {"KILLED" if killed else "survived"}',
              flush=True)

    # report
    lines = [f'# E4 mutation sensitivity -- {name}\n',
             f'Baseline verdict: `{base}`\n',
             '| Operator | Killed | Total | Kill rate |',
             '|---|---|---|---|']
    tk = tt = 0
    labels = {'CP': 'contact polarity', 'CO': 'coil-op (OTE->OTL)',
              'LR': 'latch-retention drop', 'GC': 'guard-contact drop',
              'TK': 'timer-kind swap'}
    for op in ('CP', 'CO', 'LR', 'GC', 'TK'):
        if op in tally:
            k, t = tally[op]; tk += k; tt += t
            lines.append(f'| {op} ({labels[op]}) | {k} | {t} | {100*k//t if t else 0}% |')
    lines.append(f'| **overall** | **{tk}** | **{tt}** | **{100*tk//tt if tt else 0}%** |')
    if survivors:
        lines.append(f'\nSurvivors (equivalent or undetected): {", ".join(survivors)}')
    report = '\n'.join(lines) + '\n'
    with open(os.path.join(HERE, f'results_{name}.md'), 'w') as f:
        f.write(report)
    print('\n' + report)


if __name__ == '__main__':
    main()
