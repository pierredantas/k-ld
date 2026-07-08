# WP2 — independent verdict validation (NuSMV 2.6.0)

Hand-written SMV encodings of three representative family members' faithful
semantics, checked with real NuSMV (BDD symbolic). Confirms the expected labels in
`../coverage.md` are correct, spanning all three property kinds and both verdicts.

| Member | Property kind | Expected | NuSMV result |
| --- | --- | --- | --- |
| `ton_chain2`   | mutual_exclusion | safe   | `invariant !(P1 & P2)  is true` |
| `tof_hold`     | invariant        | unsafe | `invariant (Light -> (Pir \| Button))  is false` |
| `ctu_saturate` | absence          | safe   | `invariant !(Done & Reset)  is true` |

Reproduce: `NUSMV=/path/to/NuSMV bash reproduce.sh`

These SMV models encode the *faithful* timer/counter semantics (as K-ESBMC implements
them) to check the family's labels independently of K. The full 15-program family is
run through the K-ESBMC oracle via `../../rung6/differential.py`.
