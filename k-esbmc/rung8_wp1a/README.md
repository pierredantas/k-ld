# WP1a — MATIEC-C + CBMC as an independent second verifier

**Purpose.** The paper's differential study (RQ2/RQ3) rests on a *single* verifier,
ESBMC-PLC, whose LD→GOTO front-end comes from the authors' own line. The strongest
reviewer objection (review W5) is that the generality claim is asserted, not shown.
WP1a adds a **second, independent verification path** over the same benchmarks:

```
PLCopen XML --[MATIEC: iec2c]--> C --[CBMC]--> SAFE / VIOLATED
```

MATIEC's LD→C lowering is different from **both** ESBMC-PLC's LD→GOTO **and** K-ESBMC's
`plcopen2kld.py`. So a verdict from this path is a genuinely independent second
opinion — and, because MATIEC models timers faithfully, on the three known
disagreements it is expected to **side with K-ESBMC**, converting "our oracle says so"
into "an independent MATIEC+CBMC engine says so too." It reuses the *exact* OpenPLC
container the RQ1 validation already pulls MATIEC from (`../validation/run.sh`), so it
adds no new trusted component.

## Files

| File | Role | Runs without Docker? |
| --- | --- | --- |
| `gen_cbmc_harness.py` | Verifier-independent core: reads `<prog>.json` (var kinds) + `props.yaml`, emits a bounded-scan CBMC harness with nondet inputs and one `__CPROVER_assert` per property. | ✅ yes |
| `gen_bindings_stub.py` | Auto-writes `bindings.h` by joining the PLCopen XML (name→`%IX0.0`) with `LOCATED_VARIABLES.h` (`%IX0.0`→`__IX0_0`). Flags non-located locals referenced by properties as UNRESOLVED rather than dropping them. | ✅ yes |
| `run_wp1a.sh` | Full pipeline on the paper's PLCopen-XML benchmarks: compile XML → C via MATIEC in the container, generate the harness + bindings, run CBMC. | ❌ needs Docker |
| `smoke/` | Harness-core validation on the paper's `Btn→TON→Light` probe (§4.3): faithful vs havoc timer, driven by **real CBMC** and by a native sweep. | ✅ yes (real CBMC) |
| `matiec_cbmc/` | **WP1a executed end-to-end with the real toolchain** — real `iec2c` → real MATIEC-generated C → real CBMC. See `matiec_cbmc/RESULTS.md`. | ✅ yes (real CBMC + real iec2c) |

## What is validated here vs. what still needs Docker

**Executed locally this session with real tools (CBMC 6.10.0 + MATIEC `iec2c` built
from source):**

- **`matiec_cbmc/` — the real end-to-end path.** Real `iec2c` compiles ST → C; real
  CBMC checks the genuine MATIEC-generated C. Faithful scan-TON → property A
  **VERIFICATION SUCCESSFUL** (proved, loop fully unwound); havoc timer → property A
  **VERIFICATION FAILED** (the ESBMC false alarm). See `matiec_cbmc/RESULTS.md`. This is
  WP1a's claim on genuine MATIEC codegen, not a hand model — two independent engines
  (K-ESBMC and MATIEC-C+CBMC) agree against ESBMC.
- **`smoke/` — the harness-core check** on the paper's probe, run under **real CBMC**:
  faithful model → `prop A: SUCCESS`; havoc model → `prop A: FAILURE`. Confirms the
  generator's property compilation is sound independently of MATIEC.

Reproduce the smoke core (real CBMC is the default; `-DWP1A_NATIVE` gives the random sweep):
```bash
cd smoke
python3 ../gen_cbmc_harness.py mt.json props.yaml --scans 6 > harness.c
# real bounded model checking:
cbmc harness.c model_faithful.c --unwind 8 --no-unwinding-assertions   # prop A SUCCESS
cbmc harness.c model_havoc.c    --unwind 8 --no-unwinding-assertions   # prop A FAILURE
# optional native random sweep:
gcc -DWP1A_NATIVE -std=gnu99 -w harness.c model_faithful.c nondet_native.c -o sf && ./sf
```
Reproduce the real MATIEC path: see `matiec_cbmc/RESULTS.md`.

**Still needs Docker + the original benchmarks (the remaining integration work):**

1. **The PLCopen XML sources.** The `.ld` files vendored in `../rung6` are already
   *K-ESBMC DSL*; `run_wp1a.sh` needs the **original PLCopen XML** ESBMC consumes (from the
   ESBMC-PLC benchmark repo). Drop them in and pass the path.
2. **The XML→ST→C step for graphical LD.** `iec2c` compiles textual IEC; a graphical LD
   body is turned into ST by OpenPLC's editor/build step. `run_wp1a.sh` invokes OpenPLC's
   own `compile_program.sh` to do this and collect `Res0.c`. **Verify this path against
   your container's actual layout** — it is the one step most likely to need a tweak
   (script name / generated-file locations differ across OpenPLC builds).
3. **`bindings.h`** — mapping `VAR(x)` onto the MATIEC located-variable symbol (`__IX0_0`,
   `__QX0_1`, …). `gen_bindings_stub.py` auto-writes it from the XML + `LOCATED_VARIABLES.h`;
   `run_wp1a.sh` calls it automatically and **aborts if any property references a non-located
   local** (those live inside a POU instance struct and need one hand-written `#define`). A
   human should confirm the located-variable map before trusting a verdict. If your OpenPLC
   build declares located vars as pointers, compile with `-DWP1A_LOCATED_POINTERS`.

## Suggested first real run

Start with the two decisive benchmarks so the payoff is immediate:

- `traffic_light` (havoc false alarm) — expect MATIEC-C+CBMC = **SAFE**, agreeing with
  K-ESBMC against ESBMC's spurious counterexample.
- `stairs_light` (skip / missed bug) — expect MATIEC-C+CBMC = **VIOLATED**, agreeing with
  K-ESBMC against ESBMC's unsound `SUCCESSFUL`.

Two agreements there would let the paper report the three disagreements as corroborated by
**two** independent engines (K-ESBMC *and* MATIEC-C+CBMC) plus the OpenPLC runtime tie-breaker
— a materially stronger RQ3.
