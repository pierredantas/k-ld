# Rung 6 — E3 Differential Oracle (K-ESBMC vs ESBMC LD→GOTO)

Three engines on each benchmark:
1. **ESBMC** `esbmc bench.ld --ld-props props.yaml` — the LD→GOTO path under test.
2. **K-ESBMC** (`differential.py`) — exhaustive reachability oracle: drives every input
   combination each scan via `krun`, BFS to a fixpoint over the finite retained-state
   space, checks each property invariant on every reachable image → SAFE / VIOLATED+witness.
3. **OpenPLC/MATIEC** (`../validation/`) — external tie-breaker when 1 and 2 disagree.

## Pipeline

```
plcopen2kld.py  bench.ld  sidecar.json   # PLCopen XML -> K-ESBMC DSL (+ in/out/local classification)
differential.py prog.ld  sidecar.json  props.yaml   # K-ESBMC verdict per property
```

Two frontends (both independent of ESBMC):
- `plcopen2kld.py` — **simple rung format** (linear <contact> series + <coil>, TON/TOF/TP).
- `graphical2kld.py` — **graphical netlist** (power rails + contacts/coils/blocks wired by
  refLocalId): series=AND, parallel=OR, coils→OTE/OTL/OTU, TON/TOF/TP block outputs read as
  `XIC(<inst>_Q)`, and edge contacts (`edge="rising"/"falling"`) modelled with prev-value
  helper coils. Tolerates undeclared XML namespace prefixes.

The frontend emits all standard FBs: TON/TOF/TP, CTU/CTD, and R_TRIG/F_TRIG (the
edge-FBs are lowered to the same prev-value helper pattern as edge contacts). The
harness also handles property `kind: mutual_exclusion` (synthesised as absence of any
pair both true).

### Graphical-frontend coverage
| Benchmark | Status |
|-----------|--------|
| stairs_light  | ✅ full — auto-translation reproduces the P1 violation identically to the hand-version |
| water_control | ✅ full — seal-in pump logic (series/parallel OTL/OTU) |
| beremiz_traffic_light | ✅ full — TON + R_TRIG cycle; runs, all 3 props checked (both engines SAFE) |
| dimmer        | ⚠ near-full — TON/TOF/TP + CTU ok; one non-standard block (`*_OUT`) still dangling |
| beremiz_bacnet | ✗ no `<LD>` body (FBD — out of scope) |

Remaining: dimmer's non-standard block; auto-snapshot set/reset coil pairs (same-scan
toggle race); real timer presets when PT is a variable rather than an inVariable literal.

## Method notes (learned the hard way)

- **krun startup ≈ 27 s under amd64 emulation** → per-transition BFS is infeasible.
  `differential.py` instead pays startup ONCE: one long input trace (all input
  combinations × N sweeps) in a single krun call, checking each property on every
  per-scan image in the `<trace>` cell. Bounded, but fairly matches ESBMC's bounded
  unwind. (An exhaustive-BFS variant is kept in git history for the small combinational
  benchmarks.)
- **Property `kind` matters.** props.yaml mixes `kind: invariant` (expr must always
  hold) and `kind: absence` (expr is a BAD condition that must never hold). The harness
  MUST branch on kind, else `absence` props (e.g. `Alarm_Overfill && Fill_Valve`) look
  trivially violated at the all-false init. Honoring kind is what makes the comparison
  to ESBMC valid.

## Results so far

| Benchmark | ESBMC | K-ESBMC | Agree | Notes |
|-----------|-------|------|-------|-------|
| tank_level_control (safe)   | SUCCESSFUL | P2–P5 SAFE | ✅ | exhaustive: 3 reachable states |
| tank_level_control (unsafe) | FAILED     | P2,P3 VIOLATED (+witness) | ✅ | witness PUMP∧HIGH_SWITCH, VALVE∧LOW_SWITCH |
| bottle_filling (safe)       | SUCCESSFUL | P1–P6 SAFE-to-bound | ✅ | **timer TON modelled** (PT=2); ESBMC skips it, still agree |
| bottle_filling (unsafe)     | FAILED     | P1,P2 VIOLATED + absence P4,P6 VIOLATED; P3,P5 safe | ✅ | witnesses valve∧¬bottle, valve∧full; P3/P5 correctly still-safe (E-stop protection survives via System_Running) |
| beremiz_traffic_light       | SUCCESSFUL (skips FB blocks) | P1–P3 SAFE-to-bound | ✅ | graphical; TON + R_TRIG cycle modelled by K-ESBMC, skipped by ESBMC; no divergence on these props |
| stairs_light (graphical)    | SUCCESSFUL (skips TOF) | **P1 VIOLATED @scan2** | ❌ **missed bug** | see FINDINGS.md — ESBMC unsound (drops the off-delay timer) |

Note on bottle_filling: ESBMC *skips* the TON block yet still agrees, because none of
its properties actually diverge on the timer path within the bound. The timer-skip
discrepancy will surface on benchmarks whose properties depend on a timer output.

## Next
- Other simple-format benchmarks: elevator, traffic_light (safe+unsafe).
- Hunt the timer-skip discrepancy: a benchmark/property that depends on a timer output.
- Graphical-netlist frontend (stairs_light, dimmer, beremiz_*, water_control).
- OpenPLC as tie-breaker on any disagreement.
