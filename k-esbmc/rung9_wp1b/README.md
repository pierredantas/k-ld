# WP1b — an independent engine (NuSMV) cross-checks the timer disagreement

**Purpose.** Strengthen the differential beyond a single verifier (review W5) by
checking the timer disagreement with a *different verification engine*. Where WP1a
adds MATIEC-C + CBMC (SAT-BMC), WP1b adds **NuSMV** — **BDD symbolic model
checking**, a fundamentally different algorithm (symbolic fixpoint, not bounded
unrolling), whose invariant proofs are **unbounded**.

## What ran (executed with real NuSMV 2.6.0)

Same `Btn→TON→Light` probe as WP1a, encoded in SMV two ways:

| Model | NuSMV invariant `Light → Btn` |
| --- | --- |
| `faithful.smv` — scan-TON (K-ESBMC semantics; `et` resets when `Btn` low) | **is true** — proved (unbounded) |
| `havoc.smv` — timer output left free (`Qfree`) | **is false** — CEX `Btn=F, Qfree=T, Light=T` |

Reproduce (NuSMV is open source: <https://nusmv.fbk.eu/distrib/>):
```bash
NUSMV=/path/to/NuSMV bash reproduce.sh
# faithful : -- invariant (Light -> Btn)  is true    [expected: is true]
# havoc    : -- invariant (Light -> Btn)  is false   [expected: is false]
```

## Why this matters

- **Three independent engines now agree against ESBMC.** K-ESBMC (reachability),
  MATIEC-C+CBMC (SAT-BMC, WP1a), and NuSMV (BDD, WP1b) all find property A safe
  under a faithful timer and violated under havoc — the ESBMC false alarm is not an
  artifact of any one verification style.
- **The NuSMV proof is unbounded**, so it also buys down the bounded-horizon threat
  (review W7): the faithful result is a complete proof over all reachable states,
  not safe-up-to-horizon.

## Honest scope

This is an independent **engine**, not an independent **front-end**: we author the
SMV model, so — unlike a third-party LD verifier — it does not test another tool's
*timer handling*. It therefore corroborates the disagreement's direction and rules
out a BMC-specific artifact, but does not by itself show that other front-ends also
fumble timers. The intended independent-front-end tool (PLCverif) could not ingest
our PLCopen LD format, and Arcade.PLC is no longer distributed — see `PLCVERIF.md`.
Standing up a third-party LD verifier remains the strongest future extension; the
differential harness is ready to accept its verdicts.

## Files
- `faithful.smv`, `havoc.smv` — the two SMV models.
- `reproduce.sh` — runs both, prints verdicts.
- `PLCVERIF.md` — why PLCverif/Arcade.PLC were not usable.
- `RESULTS.md` — recorded outcomes.
