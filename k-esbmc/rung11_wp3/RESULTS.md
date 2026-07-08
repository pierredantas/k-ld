# WP3 — fault-injection campaign over the WP2 family

Five translation-fault operators (rung7) over the 15-program WP2 family, classified with the validated `ld_exec` oracle (`validate_exec.py`: it reproduces the RQ1 reference traces and all WP2 labels).

## Per-operator detection

| Op | Fault class | Mutants | Behavioral | Property | Beh% | Prop%(of beh) |
| --- | --- | --- | --- | --- | --- | --- |
| CP | contact-polarity | 49 | 39 | 17 | 80% | 44% |
| CO | coil-op OTE->OTL | 20 | 20 | 8 | 100% | 40% |
| LR | latch-retention drop | 4 | 4 | 2 | 100% | 50% |
| GC | guard-contact drop | 9 | 6 | 3 | 67% | 50% |
| TK | timer-kind TON<->TOF | 5 | 4 | 2 | 80% | 50% |
| **Σ** | | **87** | **73** | **32** | **84%** | **44%** |

**Property-adequacy gap:** of 73 behavior-changing mutants the benchmark properties detect only 32 (**44%**) -- the oracle sees every observable fault; a property catches one only when it constrains the affected variable.

## The previously-inert operators now fire

In the original tank+bottle study (rung7) **LR fired 0 times and TK once** (on dead code). Over the WP2 family **LR fires 4 times and TK 5 times**, exercising latch-retention and timer-kind faults that the public suite could not.

## Per-program

| Program | Mutants | Behavioral | Property |
| --- | --- | --- | --- |
| `comb_and` | 6 | 6 | 6 |
| `comb_mixed` | 5 | 5 | 3 |
| `comb_or` | 3 | 3 | 3 |
| `ctd_load` | 4 | 2 | 1 |
| `ctu_saturate` | 4 | 2 | 1 |
| `edge_counter` | 10 | 8 | 1 |
| `ftrig_edge` | 8 | 8 | 3 |
| `latch_basic` | 4 | 4 | 2 |
| `rtrig_edge` | 8 | 7 | 4 |
| `seal_in` | 5 | 5 | 3 |
| `timer_latch_mix` | 6 | 5 | 1 |
| `tof_hold` | 5 | 5 | 1 |
| `ton_chain2` | 12 | 7 | 1 |
| `ton_single` | 4 | 3 | 2 |
| `tp_pulse` | 3 | 3 | 0 |

_Oracle: validated `ld_exec` (krun unavailable in this environment); the canonical run is `rung6/differential.py` under K._
