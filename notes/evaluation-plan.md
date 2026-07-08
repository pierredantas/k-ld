# K-LD — Evaluation-Broadening Plan (TOSEM)

**Goal.** Convert the paper's weakest dimension — a differential built on a *single*,
in-group verifier over 13 programs — into a strength, so the central methodological claim
("an executable reference semantics can *audit* any translation-based LD verifier") is
**demonstrated**, not asserted. Target venue is **TOSEM**; scope fit is already Strong, so
this plan is purely about evaluation credibility, not repositioning.

Each work package (WP) closes a named weakness from the peer review (`tosem-review.md`).

| WP | Kills | One-line | Effort | Priority |
| --- | --- | --- | --- | --- |
| **WP1a** | W5 | Second verification path: MATIEC-C + CBMC | S | **P0 (executed, real tools)** |
| **WP1b** | W5, W7 | Independent engine: NuSMV (BDD). PLCverif ruled out (Siemens-only), Arcade.PLC defunct | M | **P0 (executed, NuSMV)** |
| **WP2** | W5b | Grow + *characterize* the benchmark corpus (13 → 28, synthetic family) | M | **P1 (done: family + coverage matrix, labels NuSMV-checked)** |
| **WP3** | W8 | Real fault-injection campaign (fix inert operators; mutate the translator) | M | **P1** |
| **WP4a** | W7 | Horizon-scaling + sequence-dependent violations | S | P2 |
| **WP4b** | W3 | Second-runtime cross-check (break the shared MATIEC ground truth) | S | P2 |

Where the work lands in the repo: `k-ld/validation` (RQ1), `k-ld/rung6` (E3 differential),
`k-ld/rung7` (E4 fault injection), `k-ld/proof` (RQ4), and the new `k-ld/rung8_wp1a` (WP1a).

---

## WP1a — MATIEC-C + CBMC as an independent second verifier  · kills W5 · **prototyped**

**What.** Add the path `PLCopen XML --[MATIEC iec2c]--> C --[CBMC]--> SAFE/VIOLATED`. MATIEC's
LD→C lowering differs from **both** ESBMC-PLC's LD→GOTO and K-LD's `plcopen2kld.py`, so it is
an independent second opinion — and reuses the *same* OpenPLC container RQ1 already trusts
(`validation/run.sh`), adding no new trusted component.

**Why it's high-value / low-cost.** On the three disagreements MATIEC-C+CBMC should side with
K-LD (MATIEC models timers faithfully), so RQ3 becomes "corroborated by **two** independent
engines plus the runtime tie-breaker" instead of one oracle. Almost no new tooling: the
compile path already exists in the container.

**Status (this repo). Executed end-to-end with real tools** in `k-ld/rung8_wp1a`:
- `gen_cbmc_harness.py` / `gen_bindings_stub.py` — verifier-independent harness + bindings
  generators. Validated locally.
- `matiec_cbmc/` — **real `iec2c` (built from `thiagoralves/matiec`) → real MATIEC-generated
  C → real CBMC 6.10**: faithful scan-TON proves property A **SUCCESSFUL** (siding with
  K-LD); havoc timer → property A **FAILED** (the ESBMC false alarm). See
  `matiec_cbmc/RESULTS.md`. The mechanism is demonstrated on genuine MATIEC codegen.
- `smoke/` — the same result under real CBMC on the paper's probe, isolating the harness core.

**Remaining to land it on the paper's benchmarks (needs Docker + original XML):**
1. Obtain the original **PLCopen XML** benchmarks (the repo's `.ld` are already K-LD DSL).
2. Run `run_wp1a.sh` (container `iec2c`, which loads the standard-FB library so the wall-clock
   `TON` body is used — a local bison-3.x `iec2c` does not load that library; the
   `matiec_cbmc/` demo therefore expresses the timer as the equivalent scan-counting ST).
3. Auto-stub `bindings.h` (`gen_bindings_stub.py`, already wired into `run_wp1a.sh`).
4. Run on `traffic_light` and `stairs_light` first (decisive cases), then the full suite.

**Reviewer sentence you earn:** *"Every disagreement is independently confirmed by a second
verification path (MATIEC-C + CBMC) whose front-end shares no code with either the oracle or
the tool under test."*

---

## WP1b — An independent verification engine  · kills W5, buys down W7  · **executed (NuSMV)**

**Intended.** A genuinely independent *front-end* — **PLCverif** (CERN) / **Arcade.PLC** (RWTH)
— run through the differential, to answer: do *other* verifiers also skip/havoc timers?

**What actually happened.** Neither third-party tool was usable: **PLCverif's only PLC
front-end is Siemens Step7 (SCL/STL)** — it cannot ingest our PLCopen XML LD without an
LD→STL translator (another trusted front-end, defeating the point); **Arcade.PLC is no longer
distributed** (tool page 404). Documented in `k-ld/rung9_wp1b/PLCVERIF.md`.

**Fallback executed.** An independent *engine*: **NuSMV** (BDD symbolic model checking) on the
timer probe. Faithful scan-TON → invariant `Light → Btn` **true** (proved, **unbounded**);
havoc → **false** with counterexample. So three engines — K-LD (reachability), MATIEC-C+CBMC
(SAT-BMC, WP1a), NuSMV (BDD, WP1b) — agree against ESBMC, and NuSMV's unbounded proof also
buys down the bounded-horizon threat (W7). Implemented in `k-ld/rung9_wp1b/`.

**Honest boundary.** Independent *engine*, not independent *front-end*: it rules out a
BMC-specific artifact but does not test another tool's timer handling. A third-party LD
verifier remains the strongest future extension; the harness is ready to accept its verdicts.

**Deliverable.** Extend Table 3 to a multi-engine matrix (columns = ESBMC-PLC / K-LD /
MATIEC-C+CBMC / NuSMV / OpenPLC-tiebreak).

---

## WP2 — Grow and characterize the benchmark corpus  · kills W5b

**What.** 13 → ~35–45 programs, with **documented construct coverage** (the win is coverage,
not raw N).

- **Sources:** OSCAT function-block library, PLCopen example set, more Beremiz examples,
  OpenPLC community/GitHub LD programs, the MATIEC test suite.
- **Controlled synthetic family** (most important): systematically vary the hard constructs —
  `TON` chains length 1..n, `CTU`/`CTD` at and over preset (saturation), `TOF` hold windows,
  `R_TRIG`/`F_TRIG`, and mixed timer+latch controllers — so the constructs where bugs live are
  *guaranteed* exercised. Directly answers "your suite has a dead timer" (§4.4).

**Deliverable.** A coverage table (programs × {contacts, latch, TON/TOF/TP, CTU/CTD, edge,
format, property-kind}) proving systematic — not lucky — coverage.

**Status — done (synthetic family).** Implemented in `k-ld/rung10_wp2/`: a generator
(`gen_family.py`) emits **15 programs** (corpus 13 → 28) as `.ld`/`.json`/`.props.yaml`
triples in the harness's format, plus `coverage.md` — the programs × constructs ×
property-kinds matrix (every construct column ≥1 program; all three property kinds; 13
safe / 2 unsafe-under-faithful-timer). Ready to run through `rung6/differential.py` under K.
Labels independently confirmed for three representative members (one per property kind,
both verdicts) with real NuSMV (`validate/`): `ton_chain2` safe, `tof_hold` unsafe,
`ctu_saturate` safe — all matched. Not yet done: external real-world corpus (OSCAT/PLCopen/
MATIEC suite) and graphical-format variants — mechanical follow-ups.

---

## WP3 — A real fault-injection campaign  · kills W8

Current study (`rung7`): 2 benchmarks, 60 mutants, latch operator never fires, timer once.

**Fixes:**
1. **Feed the inert operators** — include latch-heavy and timer-heavy programs (draw from
   WP2) so all five operators fire across many mutants.
2. **Stronger variant — mutate the *translator*, not the diagram.** Inject single-point faults
   into ESBMC-PLC's LD→GOTO code (or the front-ends) and measure the fraction K-LD's
   whole-behavior oracle catches vs. the fraction the shipped property suites catch. This is a
   far sharper statement of the property-adequacy gap and is squarely TOSEM-flavored
   (mutation testing of a translation).
3. **Report per-operator detection rates** over hundreds of mutants with confidence intervals.
   The 27% figure becomes a defensible curve, not an anecdote.

---

## WP4 — Two hardening items (do if time allows)

**WP4a — bounded-sampling threat (W7).** Add a horizon-scaling study (vary trace length /
`--unwind`, show verdict stability) and include a couple of **sequence-dependent** violations
(e.g. a counter that only overflows under a specific input ordering) to demonstrate the harness
catches more than memoryless per-scan faults. Tighten the §4.5 threat wording accordingly.

**WP4b — shared ground truth (W3).** Cross-validate a few function blocks against a runtime
**independent of MATIEC** — Beremiz's runtime or a CODESYS demo/simulator — so "matches
deployed behavior" no longer rests on a single implementation. Even 2–3 blocks materially
weakens the circularity objection.

---

## Explicit non-goals (scope discipline)

- **Do not** close the timer/counter `kprove` mechanization (W4) inside this evaluation effort —
  it is a proof task; keep it as clearly-scoped future work.
- **Do not** add integer/analog data support — that is a TECS-style ask, a large new fragment,
  and unnecessary for TOSEM.
- **Do not** chase >50 benchmarks — a second verifier (WP1b) and documented coverage (WP2) beat
  raw N for a reviewer.

---

## Two execution tracks

**Minimal (time-boxed, still satisfies the core objection):** WP1a (finish) + WP2 (to ~30 with
coverage table) + WP3 per-operator reporting. Converts W5 from near-fatal to addressed.

**Strong (accept posture):** add WP1b (the real second verifier) + WP4. WP1b is what turns the
generality *claim* into a generality *result*.

## Revised RQ structure this implies

- **RQ1** (fidelity) — unchanged; + WP4b second-runtime cross-check.
- **RQ2/RQ3** (differential) — now **multi-verifier**: ESBMC-PLC, MATIEC-C+CBMC, and
  PLCverif/Arcade.PLC → a much stronger Table 3, disagreements corroborated by ≥2 engines.
- **RQ-new** — "Does the oracle expose translation faults that shipped property suites miss?"
  (the mutate-the-translator campaign, WP3).
- **RQ4** (mechanization) — unchanged, honestly scoped to the combinational/latch fragment.
