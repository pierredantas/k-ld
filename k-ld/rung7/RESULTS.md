# E4 — Fault Injection and the Property-Adequacy Gap

We inject single-point *translation-rule* faults into K-ESBMC programs (see `mutate.py`)
and ask two questions of each mutant: does it change observable behavior (the oracle's
full per-scan trace), and does it flip any of the benchmark's own safety properties?
The gap between the two answers is the finding.

## Operators
| Op | Fault class | Mutation |
|----|-------------|----------|
| CP | contact polarity | `XIC(x)` ↔ `XIO(x)` |
| CO | coil operation | `OTE` → `OTL` |
| GC | guard-contact drop | remove one series `* XI?(...)` term |
| LR | latch-retention drop | `OTL/OTU` → `OTE` (no latched coils in these two benchmarks) |
| TK | timer-kind swap | `TON` ↔ `TOF` |

## Results (60 mutants over `tank_level_control` + `bottle_filling`)

| Detection level | tank (20) | bottle (40) | combined (60) |
|---|---|---|---|
| **Behavioral** (trace changes) | 17 (85%) | 23 (57%) | **40 (66%)** |
| **Property** (flips a benchmark safety property) | 6 (30%) | 5 (12%) | **11 (18%)** |
| Equivalent (no observable change) | 3 | 17 | 20 (33%) |

**Of the 40 behavior-changing (non-equivalent) mutants, the benchmarks' safety
properties detect only 11 — 27%.**

## Interpretation: property adequacy, not oracle sensitivity

- The **oracle distinguishes every non-equivalent mutant** (by construction, a
  differing trace yields a differing signature). What varies is whether a benchmark
  *property* observes the change.
- The **27% property-detection of real behavioral faults** is the finding: the safety
  properties shipped with these programs observe only a fraction of behavior. A
  translation fault is caught by a property-based verifier **only when a property
  happens to constrain the affected variable.**
- This is exactly the blind spot that lets verifier translation defects escape.
  Where the properties observe the timer (`stairs_light`, `traffic_light`), the oracle
  **found** the ESBMC defects; where they do not (`tank`, `bottle`), a fault passes
  silently.

## Concrete illustration: a dead timer

In `bottle_filling`, `OTE(Filling_Done) := XIC(TON1_Q)` is immediately overwritten by
`OTE(Filling_Done) := XIC(Level_Full)` (last-wins), so the timer output `TON1_Q` is
**dead code**. This is why the `TON`→`TOF` mutation (TK) is behaviorally equivalent,
why no property flips, **and why ESBMC skipping this timer is harmless** for this
program. The oracle makes the deadness visible; a property-only view cannot.

## Threats
Two benchmarks (chosen for a fast combinational and a timer case); the LR operator
never fires (neither uses latched coils) and TK fires once (a dead timer), so the
timer/latch fault classes are under-exercised here. Detection is measured against the
public benchmark properties and a bounded, input-sampled trace. The conclusion---that
property coverage, not the oracle, bounds fault detection---is robust to these limits
and is corroborated by the in-the-wild discrepancies of the main study.

## Reproduce
```
python3 mutate.py <prog>.ld mut_<name>            # generate single-point mutants
python3 run_mutation.py <name> <prog>.ld <side>.json <props>.yaml   # property-level
python3 run_behavioral.py <name> <prog>.ld <side>.json              # behavioral (trace)
```
