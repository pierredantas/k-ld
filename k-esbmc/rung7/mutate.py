#!/usr/bin/env python3
"""
E4 mutation operators for K-ESBMC programs.

Each operator injects one systematic *translation-rule* fault into a K-ESBMC DSL
program---the kind of mistake a diagram-to-model front-end can make. Given a
program, we enumerate every single-point mutant for each operator. The differential
(differential.py) then verifies each mutant against the property suite; a mutant is
"killed" iff its per-property verdict differs from the original. The kill rate
measures how sensitively the oracle + benchmark properties detect translation faults,
which is what makes an agreement in the main study non-vacuous.

Operators (fault class -> mutation):
  CP  contact polarity     XIC(x) <-> XIO(x)   (normally-open/closed swapped)
  CO  coil operation       OTE <-> OTL         (momentary vs latch)
  LR  latch retention drop OTL->OTE, OTU->OTE  (retained coil made momentary)
  GC  guard-contact drop   remove one "* XIC/XIO(...)" term from a rung
  TK  timer-kind swap      TON<->TOF           (on-delay vs off-delay)

Usage: mutate.py <prog.ld> <outdir>   ->  writes <outdir>/<op>_<n>.ld, prints a manifest
"""
import sys, re, os, itertools


def contacts_polarity(line):
    """Yield (mutated_line,) for each XIC/XIO occurrence flipped, one at a time."""
    for m in re.finditer(r'\b(XIC|XIO)\(', line):
        alt = 'XIO(' if m.group(1) == 'XIC' else 'XIC('
        yield line[:m.start()] + alt + line[m.end():]


def coil_op(line):
    # OTE(v) := ...  ->  OTL(v) := ...   (only at the coil head)
    m = re.match(r'\s*OTE\(', line)
    if m:
        yield line.replace('OTE(', 'OTL(', 1)


def latch_drop(line):
    for op in ('OTL', 'OTU'):
        if re.match(rf'\s*{op}\(', line):
            yield re.sub(rf'^(\s*){op}\(', r'\1OTE(', line, count=1)


def guard_drop(line):
    """Remove one series term '* XIC(...)' or '* XIO(...)' from an OTE/OTL/OTU rung."""
    # only mutate combinational coil rungs (has ':=' and at least one '*')
    if ':=' not in line or ' * ' not in line:
        return
    for m in re.finditer(r'\s\*\s(XI[CO]\([^)]*\))', line):
        yield line[:m.start()] + line[m.end():]


def timer_kind(line):
    m = re.match(r'\s*(TON|TOF)\(', line)
    if m:
        alt = 'TOF(' if m.group(1) == 'TON' else 'TON('
        yield re.sub(r'^(\s*)(TON|TOF)\(', rf'\g<1>{alt}', line, count=1)


OPS = {'CP': contacts_polarity, 'CO': coil_op, 'LR': latch_drop,
       'GC': guard_drop, 'TK': timer_kind}


def main():
    prog, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    lines = open(prog).read().splitlines(keepends=False)
    manifest = []
    for op, fn in OPS.items():
        n = 0
        for i, line in enumerate(lines):
            for mut in fn(line):
                if mut == line:
                    continue
                variant = lines[:i] + [mut] + lines[i+1:]
                name = f'{op}_{n}'
                with open(f'{outdir}/{name}.ld', 'w') as f:
                    f.write('\n'.join(variant) + '\n')
                manifest.append(f'{name}\t{op}\tline{i+1}\t{line.strip()}  =>  {mut.strip()}')
                n += 1
    print('\n'.join(manifest))
    sys.stderr.write(f'# {len(manifest)} mutants written to {outdir}\n')


if __name__ == '__main__':
    main()
