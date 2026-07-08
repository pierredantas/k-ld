# WP3 — fault-injection campaign that exercises the inert operators

**Purpose.** The original fault-injection study (`rung7`) ran five translation-fault
operators over `tank_level_control` + `bottle_filling`, but those programs have **no
latched coils and one dead timer**, so the latch-retention (LR) and timer-kind (TK)
operators barely fired (LR 0×, TK 1×). WP3 fixes this by running the same operators
over the latch- and timer-heavy **WP2 family**, and reports per-operator detection
with the operators actually firing (review W8).

## Result (see `RESULTS.md`)

87 mutants over the 15-program family:

| | Mutants | Behavioral | Property |
| --- | --- | --- | --- |
| **Σ (all 5 operators)** | 87 | 73 (84%) | 32 (44% of behavioral) |
| LR (latch-retention drop) | **4** (was 0) | 4 | 2 |
| TK (timer-kind swap) | **5** (was 1) | 4 | 2 |

- **The inert operators now fire:** LR 4× and TK 5× (vs 0× / 1× in `rung7`),
  exercising latch- and timer-translation faults the public suite could not.
- **Property-adequacy gap holds even here:** of 73 behavior-changing mutants the
  properties detect only 44% — and this family's properties were *designed to
  observe* the construct under test. On the real benchmarks (`rung7`) the figure is
  27%. Either way, a property-based verifier catches a translation fault only when a
  property happens to constrain the affected variable — the blind spot behind the
  ESBMC defects (paper §4.4).

## The measurement oracle (`ld_exec.py`)

K-ESBMC's `krun` is the canonical oracle but is not installed in the authoring
environment, so the campaign uses `ld_exec.py` — a faithful re-implementation of the
K-ESBMC scan-cycle semantics (contacts, OTE/OTL/OTU retention, TON/TOF/TP, CTU/CTD, edges
via prev-value). It is **validated** (`validate_exec.py`) two ways:

1. it reproduces the paper's **RQ1 reference done-bit traces** (Table 2 / the MATIEC
   ground truth) for `TON`/`TOF`/`TP`/`CTU`/`CTD` **exactly** — the validation is
   discriminating: it caught an off-by-one in an early `TON` (`ET` measured from the
   trigger edge), the very error RQ1 describes;
2. it produces the **WP2 family's expected verdicts** on all 15 programs, and those
   verdicts agree with the independent **NuSMV** checks in `rung10_wp2/validate/`
   (`ton_chain2` safe, `tof_hold` unsafe, `ctu_saturate` safe).

## Files
- `ld_exec.py` — validated scan-cycle executor (the measurement oracle).
- `wp3lib.py` — trace generation + property evaluation (matches `differential.py`).
- `validate_exec.py` — RQ1-trace + WP2-label validation of `ld_exec`.
- `mutate_campaign.py` — runs `rung7`'s operators over the family, writes `RESULTS.md`.
- `reproduce.sh` — validate then run the campaign.

```bash
bash reproduce.sh
```

## Honest scope
`ld_exec` is a WP3 measurement instrument, validated against the RQ1 ground truth and
NuSMV; the canonical evaluation runs through `rung6/differential.py` under K. The
"mutate the translator itself" variant (injecting faults into ESBMC's LD→GOTO code
rather than the diagram), noted in the plan, needs the full ESBMC toolchain and remains
future work.
