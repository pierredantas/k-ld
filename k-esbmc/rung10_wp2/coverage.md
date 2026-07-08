# WP2 synthetic family -- construct coverage matrix

15 programs, DSL (simple/rung) format. ✓ = construct exercised. `kinds` lists the property kinds; `exp.` is the expected verdict under a faithful timer.

| Program | contacts | XIO | OR | latch | seal-in | TON | TOF | TP | CTU | CTD | edge | kinds | exp. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `comb_and` | ✓ |  |  |  |  |  |  |  |  |  |  | invariant | safe |
| `comb_or` | ✓ |  | ✓ |  |  |  |  |  |  |  |  | invariant | safe |
| `comb_mixed` | ✓ | ✓ | ✓ |  |  |  |  |  |  |  |  | invariant | safe |
| `latch_basic` |  |  |  | ✓ |  |  |  |  |  |  |  | absence | safe |
| `seal_in` | ✓ | ✓ | ✓ |  | ✓ |  |  |  |  |  |  | invariant | safe |
| `ton_single` |  |  |  |  |  | ✓ |  |  |  |  |  | invariant | safe |
| `ton_chain2` |  | ✓ |  |  |  | ✓ |  |  |  |  |  | mutual | safe |
| `tof_hold` |  |  | ✓ |  |  |  | ✓ |  |  |  |  | invariant | unsafe |
| `tp_pulse` |  |  |  |  |  |  |  | ✓ |  |  |  | invariant | unsafe |
| `ctu_saturate` |  |  |  |  |  |  |  |  | ✓ |  |  | absence | safe |
| `ctd_load` |  |  |  |  |  |  |  |  |  | ✓ |  | absence | safe |
| `rtrig_edge` | ✓ | ✓ |  |  |  |  |  |  |  |  | ✓ | invariant | safe |
| `ftrig_edge` | ✓ | ✓ |  |  |  |  |  |  |  |  | ✓ | invariant | safe |
| `timer_latch_mix` |  |  |  | ✓ |  | ✓ |  |  |  |  |  | absence | safe |
| `edge_counter` | ✓ | ✓ |  |  |  |  |  |  | ✓ |  | ✓ | absence | safe |
| **Σ** | 7 | 6 | 4 | 2 | 1 | 3 | 1 | 1 | 2 | 1 | 3 |  |  |

**Verdict mix:** 13 safe, 2 unsafe-under-faithful-timer (`tof_hold`, `tp_pulse` -- the timer-hold cases that a skipping/havocing front-end mishandles).
