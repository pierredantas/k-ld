# WP2 — a controlled synthetic benchmark family (construct coverage)

**Purpose.** The public suite (13 programs) exercises the construct fragment only
*incidentally* — its single timer is dead code (paper §4.4), so a timer-translation
fault passes silently there. WP2 adds a family that **systematically** covers every
construct, in safe and (faithfully) unsafe variants, with properties that actually
**observe** the construct under test. This closes the coverage / property-adequacy
gap the review flags (W5b, and the property-adequacy point behind W8).

## What's here

- `gen_family.py` — generator; emits the family + `coverage.md` from one spec list.
- `family/` — **15 programs**, each a triple in the exact form the differential
  harness consumes:
  - `<name>.ld` — K-ESBMC DSL (simple/rung format, per `k-esbmc/ld-syntax.k`)
  - `<name>.json` — `{ "kinds": { var: input|output|local } }`
  - `<name>.props.yaml` — properties (`invariant`/`absence` → `expression`;
    `mutual_exclusion` → `variables: [..]`)
- `coverage.md` — the programs × constructs × property-kinds matrix (auditable
  coverage; every construct column has ≥1 program, all three property kinds used).
- `validate/` — independent NuSMV cross-check of the expected verdicts.

## Coverage (see `coverage.md` for the full matrix)

Contacts (series/parallel/`XIO`), latch (`OTL`/`OTU`) + seal-in, `TON`/`TOF`/`TP`,
`CTU`/`CTD`, and edge detection (`R_TRIG`/`F_TRIG` via the prev-value helper-rung
lowering). Property kinds: `invariant`, `absence`, `mutual_exclusion`. Verdict mix:
13 safe, 2 unsafe-under-faithful-timer (`tof_hold`, `tp_pulse` — the timer-hold
cases a skipping/havocing front-end mishandles, i.e. the stairs/pulse mechanisms).

## Status — authored and label-validated; ready for the differential

K-ESBMC's interpreter (`krun`) is the primary oracle for this family:
```bash
for p in family/*.ld; do
  python3 ../rung6/differential.py "$p" "${p%.ld}.json" "${p%.ld}.props.yaml"
done
```
That step needs the K framework installed (not available in the authoring
environment). To confirm the family is real and the labels correct *without* K, we
independently checked three representative members — one per property kind, covering
both verdicts — with **real NuSMV 2.6.0** (BDD symbolic). All three matched their
expected labels (`validate/RESULTS.md`):

| Member | Kind | Expected | NuSMV |
| --- | --- | --- | --- |
| `ton_chain2` | mutual_exclusion | safe | invariant **true** |
| `tof_hold` | invariant | unsafe | invariant **false** |
| `ctu_saturate` | absence | safe | invariant **true** |

```bash
NUSMV=/path/to/NuSMV bash validate/reproduce.sh
```

## Honest scope

- The family is in the **simple/rung** DSL format (the graphical PLCopen path is
  exercised by the real benchmarks). Extending the family to graphical netlists is
  a mechanical follow-up.
- The NuSMV checks validate the *expected verdicts* of three members via
  hand-written SMV encodings of their faithful semantics; the full 15-program run
  through the K-ESBMC oracle is the primary evaluation and runs under `differential.py`.
- This grows the corpus from 13 to 28 with **documented, systematic** coverage — the
  plan's target was breadth of coverage, not raw count.
