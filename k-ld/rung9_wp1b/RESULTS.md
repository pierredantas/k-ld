# WP1b executed — results

Run with real **NuSMV 2.6.0** (BDD symbolic model checker), no registration needed.

| Model (SMV) | Engine | Invariant `Light → Btn` | Verdict |
| --- | --- | --- | --- |
| `faithful.smv` | NuSMV BDD (unbounded) | proved | **is true** |
| `havoc.smv`    | NuSMV BDD | counterexample `Btn=FALSE, Qfree=TRUE, Light=TRUE` | **is false** |

## Cross-engine summary (with WP1a)

On the timer probe, property A (`Light → Btn`, i.e. `!Light || Btn`):

| Engine | Algorithm | Faithful timer | Havoc timer |
| --- | --- | --- | --- |
| ESBMC-PLC | SMT-BMC (simple fmt) | — | **FAILED** (false alarm) |
| K-ESBMC | reachability oracle | SAFE | VIOLATED |
| MATIEC-C + CBMC (WP1a) | SAT-BMC | SUCCESSFUL | FAILED |
| **NuSMV (WP1b)** | **BDD symbolic (unbounded)** | **true** | **false** |

Three independent engines agree that a faithful timer makes property A safe and a
havoc'd timer manufactures the violation — corroborating that ESBMC's counterexample
is a modeling artifact, not a real defect. NuSMV's proof being unbounded additionally
strengthens the bounded-horizon threat to validity (review W7).

## Scope
Independent *engine*, not independent *front-end* (we author the SMV). PLCverif
(Siemens-only front-end) and Arcade.PLC (unobtainable) could not provide the
independent-front-end variant — see `PLCVERIF.md`.
