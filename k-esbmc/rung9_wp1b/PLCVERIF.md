# WP1b — why not PLCverif (or Arcade.PLC)?

WP1b's ideal is a *third-party LD verifier with its own independent front-end*, run
on our benchmarks: it would answer the sharpest question — do other verifiers also
skip/havoc timers, or model them correctly? We investigated the two obvious
candidates and neither was usable here; this note records why, so the choice of
NuSMV (an independent *engine*) is on the record.

## PLCverif (CERN) — incompatible input format

PLCverif is actively maintained (`gitlab.com/plcverif-oss`, activity July 2026) and
has a headless CLI (`cern.plcverif.cli`). But its **only PLC source front-end** is
`cern.plcverif.plc.step7` — **Siemens Step7 (SCL/STL)**. There is no PLCopen XML or
Ladder Diagram front-end.

Our benchmarks are PLCopen XML LD. To run them through PLCverif we would have to
translate LD → Siemens SCL/STL first — a large, error-prone effort that (a) is
Siemens-dialect-specific and (b) reintroduces a *trusted translator*, defeating the
independence WP1b is meant to establish. This is a structural format incompatibility
(decided by the tool's own front-end inventory), not a build hurdle.

## Arcade.PLC (RWTH) — unobtainable

Arcade.PLC's tool page (`embedded.rwth-aachen.de/.../arcade.plc`) returns HTTP 404;
the tool appears no longer distributed. Not usable.

## Consequence

A genuinely independent *front-end* is out of reach in this environment, so WP1b
falls back to an independent *engine*: NuSMV (BDD symbolic model checking), which is
a different verification algorithm from ESBMC/CBMC and gives an unbounded proof. See
`README.md` / `RESULTS.md`. Standing up a third-party LD verifier remains the strongest
future extension of WP1b; the differential harness is ready to accept its verdicts.
