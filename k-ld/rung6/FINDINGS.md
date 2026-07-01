# Rung 6 / E3 — Headline discrepancy: ESBMC havocs timer outputs

## Claim
On a Ladder program whose output is driven by a `TON` done-bit, **ESBMC treats the
timer output as unconstrained (havoc)**, producing a **false-alarm counterexample**
for a safety property that a faithful timer — K-LD, corroborated by OpenPLC — proves
safe. K-LD as the executable oracle exposes ESBMC's imprecise timer modelling.

## Minimal witness (`probe/minimal_timer.ld`)
```
Btn -> T_IN ;  TON(T_IN, PT)->T_Q ;  T_Q -> Light
```
- **Prop A** (`invariant: !Light || Btn`) — "Light on implies button held".
- **Prop B** (`absence: Light`) — "Light never on" (deliberately wrong).

| Engine | Prop A | Prop B | Timer behaviour |
|--------|--------|--------|-----------------|
| **K-LD** (faithful) | **SAFE** | VIOLATED | `Light` trace `F,F,T,T,T,F,F` — on-delay PT=2, Q only while IN held |
| **ESBMC** v8.3.0 | **VIOLATED (false alarm)** | VIOLATED | counterexample has `Btn=0, T_Q=1, Light=1` — `Q` true while `IN` false |
| **OpenPLC/MATIEC** (ref) | holds | Light does turn on | validated scan-for-scan == K-LD (see `../validation/`) |

## Why ESBMC's prop-A counterexample is spurious
ESBMC's trace asserts `T_Q = 1` while `Btn = 0` (states 6–9). For a real IEC 61131-3
`TON`, `IN = FALSE` resets the timer and forces `Q = FALSE`; `Q = TRUE` with `IN =
FALSE` is unreachable. ESBMC reaches it only because it leaves `T_Q` nondeterministic
(over-approximation) instead of modelling the on-delay state machine. The counterexample
therefore describes hardware behaviour that can never occur.

## Significance
- ESBMC's timer handling is an **over-approximation** for the simple LD format (havoc
  the FB output) and an **under-approximation** for the graphical format (skip the
  FB path entirely — see the `stairs_light` "not yet modelled" warning). Both diverge
  from IEC 61131-3; the first yields **false alarms**, the second can **miss bugs**.
- K-LD, being an executable IEC-faithful semantics (validated against OpenPLC), is a
  sound reference to detect and classify these translation gaps — exactly the E3 goal.

## Reproduce
```
python3 ../plcopen2kld.py probe/minimal_timer.ld probe/mt.json > probe/mt.ld
# K-LD: drive Btn held (T,T,T,T,T,F,F), read Light from <trace> -> F,F,T,T,T,F,F
# ESBMC: esbmc probe/minimal_timer.ld --ld-props probe/props.yaml --unwind 8 \
#          --no-unwinding-assertions   -> A and B both FAILED (A is the false alarm)
```

---

# Discrepancy 2 (the serious one): ESBMC MISSES a real violation

## Claim
On the real `stairs_light` benchmark, **ESBMC returns `VERIFICATION SUCCESSFUL`
while the program actually VIOLATES its own property P1** — because ESBMC's graphical
LD frontend *skips* the `TOF` block ("FB/timer path not yet modelled"), so it never
sees the light turn on. K-LD (faithful TOF, validated vs OpenPLC) exposes the
violation. This is an **unsound** gap (under-approximation → missed bug), strictly
worse than the havoc false-alarm above.

## Now fully automated
The `graphical2kld.py` frontend auto-translates `stairs_light.ld` (graphical netlist)
into K-LD DSL and reproduces the P1 violation **identically** to the hand-translation
below (P1 VIOLATED @scan 2). The finding no longer depends on any manual translation.

## The program (`probe/stairs.ld`, hand-translated — matches the auto-translation)
`stairs_light = TOF0_Q OR lights_buttons_state`, where the TOF is triggered by a
rising PIR edge (gated by `NOT lights_buttons_state`) with PT = 20 s. A single PIR
detection lights the stairs for the whole off-delay — the intended function — which
is exactly what P1 forbids.

P1 = `invariant: !stairs_light || stairs_pir_sensor || lights_buttons_state`.

## Result (K-LD trace; buttons unpressed, PIR pulse F,T,F,F,F,F)
| scan | pir | lights_buttons_state | stairs_light | P1 |
|------|-----|----------------------|--------------|----|
| 0 | F | F | F | holds |
| 1 | T | F | T | holds (PIR active) |
| 2 | **F** | F | **T** (TOF off-delay) | **VIOLATED** |
| 3–5 | F | F | T | VIOLATED |

- **K-LD:** P1 VIOLATED @scan 2 (light on while corridor empty, no button state).
- **ESBMC v8.3.0:** `VERIFICATION SUCCESSFUL` on `stairs_light.ld` (emits
  "graphical LD: rung path contains unsupported element 'block' … skipping path").
- **OpenPLC/MATIEC:** the TOF holds Q for PT after IN drops (validated == K-LD in
  `../validation/`), so the light stays on after the PIR clears — corroborating K-LD.

---

# Discrepancy 3: havoc false alarms on a real benchmark (traffic_light)

The full-table sweep (`results.md`) turned up two more disagreements — `traffic_light`
and `traffic_light_unsafe` (identical programs): **K-LD SAFE, ESBMC UNSAFE**. Triage:

- The program is a 4-phase light driven by a chain of 4 TONs (simple format ⇒ ESBMC
  havocs `TON1_Q..TON4_Q`). ESBMC's counterexample asserts **all four phases active
  simultaneously** (`Phase_NS_Green=Phase_NS_Yellow=Phase_EW_Green=Phase_EW_Yellow=1`),
  giving `NS_Green ∧ EW_Green` — a mutual-exclusion "violation". A real chain of TONs
  fires one phase at a time; all-active is unreachable. ⇒ **havoc false alarm.**
- K-LD run with `Enable` held for 30 scans: **0 mutual-exclusion violations**. In fact
  the program deadlocks in the NS phase (`TON2_IN = TON1_Q` is only ever a 1-scan pulse,
  so `TON2` never reaches preset and the EW phases are never entered) — a *liveness* bug,
  but no *safety* property is ever violated. K-LD SAFE is correct, and the argument is
  preset-independent.

So all three disagreements in the full table resolve in K-LD's favour, exhibiting both
of ESBMC's opposite timer-handling failures:

| Program | ESBMC | K-LD | ESBMC failure |
|---------|-------|------|---------------|
| stairs_light | SAFE | UNSAFE(P1) | **skip** timer → missed bug (unsound) |
| traffic_light (≡ _unsafe) | UNSAFE | SAFE | **havoc** timer → false alarm |

## Bottom line
The K-LD oracle (validated scan-for-scan against OpenPLC) is correct on every
disagreement, demonstrating both failure modes of ESBMC's incomplete timer translation:
- **simple LD format → havoc** the FB output → **false alarms** (minimal_timer probe; traffic_light);
- **graphical LD format → skip** the FB path → **missed violations** (stairs_light, unsound).
