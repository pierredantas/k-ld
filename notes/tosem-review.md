# ACM TCPS Peer Review — K-ESBMC (`kesbmc`)

**Manuscript:** *`kesbmc`: An Executable Formal Semantics of IEC 61131-3 Ladder Diagram for Validating Verifier Translations*
**Authors (not anonymized):** Pierre Dantas, Lucas Cordeiro (U. Manchester), Waldir Junior (UFAM)
**Target venue:** ACM Transactions on Software Engineering and Methodology (TOSEM)
**Method:** ScholarPeer 8-agent pipeline, venue = `acm` (TOSEM profile)
**Reviewed source:** `__main.tex` + `0.metadata.tex`, `_sec_text.tex`, `_sec_evaluation.tex`, `_sec_e3.tex`, `_sec_cases.tex`, `_sec_disc.tex` (reconstructed manuscript)
**Date:** 2026-07-08

---

## 0. Gating checks (read these first)

Target venue corrected to **TOSEM** (the `\acmJournal{TOSEM}` metadata was right). This removes the two most severe gates from the earlier TCPS reading (wrong-journal metadata and the 25-page hard cap). One submission-hygiene gate remains.

| Gate | Status | Evidence |
| --- | --- | --- |
| **Journal metadata** | ✅ PASS | `0.metadata.tex:6` `\acmJournal{TOSEM}` is correct for the intended venue. |
| **Double-anonymous** | ❌ FAIL (verify current policy) | TOSEM uses double-anonymous review. The class option is `[acmsmall, review]` (`__main.tex:1`) — **not** anonymized. Full author names, emails, ORCIDs, affiliations (`0.metadata.tex:14–41`) are present, and self-citations `\cite{DantasCordeiro2026artefact, DantasCordeiro2026graphical}` identify the same group as the tool under test. **Anonymize before submission** (switch to `anonymous`/`manuscript` mode, strip the author block, neutralize first-person self-citations, remove identifying repo/DOI URLs). Confirm the current requirement on the TOSEM author-guidelines page. |
| **Format** | ✅ PASS | `acmsmall` + `ACM-Reference-Format` are correct for TOSEM. |
| **Page limit** | ✅ N/A | TOSEM imposes **no strict page cap** (unlike TCPS's 25). Keep the paper concise, but length is not a desk-reject gate. |

**Scope-fit gate (TOSEM):** **Strong.** An executable formal semantics used as a differential oracle to audit a verifier's translation front-end is squarely in TOSEM's remit (software verification, program semantics, translation validation, testing methodology). The earlier CPS-scope concern does **not** apply at TOSEM.

---

## Summary

The paper introduces **`kesbmc` / K-ESBMC**, an executable formal semantics of IEC 61131-3 Ladder Diagram (LD) written in the **K framework**, extending the prior K-ST semantics of Structured Text (Wang et al., 2023) to the graphical language and its function blocks (contacts, energize/latch/unlatch coils, the retentive scan cycle, `TON`/`TOF`/`TP` timers, `CTU`/`CTD` counters, `R_TRIG`/`F_TRIG` edge blocks). Because a K definition yields both an interpreter (`krun`) and a deductive verifier (`kprove`), the authors put the same artifact to three uses:

1. **RQ1 — fidelity.** K-ESBMC's function blocks are validated **scan-for-scan** against the MATIEC/OpenPLC reference C implementations that run on real open-hardware PLCs (Table 2, exact agreement on 5 blocks).
2. **RQ2/RQ3 — differential oracle.** K-ESBMC is used as an independent reference oracle for the ESBMC-PLC LD→GOTO translation over a 13-program benchmark suite. 10/13 agree; the 3 disagreements are all ESBMC timer-translation defects, corroborated by OpenPLC, and classified into two opposite failure modes: an unsound **skip** (certifies a violating program safe — `stairs_light`) and an imprecise **havoc** (manufactures impossible counterexamples — `traffic_light`).
3. **RQ4 — mechanization.** Seven per-construct correctness lemmas for the combinational + latch fragment are machine-checked in `kprove`.

A fault-injection study (60 single-point mutants, 5 operators) argues a **property-adequacy gap**: K-ESBMC flags all 40 behavior-changing mutants, but the benchmarks' own safety properties detect only 11 (27%). The claimed broader contribution is methodological — an executable reference semantics as a general route to *audit* translation-based verifiers.

---

## Strengths

1. **Genuinely useful conceptual framing.** "A formal verifier is itself unverified code; audit its front-end with an executable reference semantics" is a clean, correct, and transferable idea. The dual interpreter/prover nature of K is exactly the right vehicle, and the paper articulates the argument well.
2. **The differential result is concrete and non-trivial.** The two opposite failure modes (skip = unsound / miss; havoc = false alarm) are a genuinely illuminating taxonomy, and the case studies (§5) walk them end-to-end with per-scan traces. The havoc-vs-skip framing is the paper's best material.
3. **Three-way corroboration.** Using OpenPLC as an external tie-breaker (rather than declaring the oracle right by fiat) is methodologically honest and materially strengthens the disagreement claims.
4. **Layered, honestly-graded assurance.** The paper is scrupulous about what is *proven* (combinational/latch), *execution-validated* (timers/counters), and *empirically validated* (end-to-end translation). This honesty is a real asset and rare.
5. **Reproducibility.** Artifact + container + "one command per table row" + Zenodo metadata (`.zenodo.json` present) meets ACM artifact expectations well — likely a strong candidate for artifact badging.
6. **The validation is shown to be discriminating** (RQ1's account of the off-by-one timer bug and the `CTU` saturation bug caught *during development*) — this pre-empts the "your check is a tautology" objection effectively.

---

## Weaknesses

### W1 — (Resolved by venue) Scope fit is Strong for TOSEM
Under the corrected TOSEM target this is **no longer a weakness.** The contribution — an executable language semantics used as a differential oracle to audit a verifier's translation front-end — is core software-engineering methodology (program semantics, translation validation, differential testing). No plant-in-the-loop / testbed / real-time-overhead evaluation is expected at TOSEM, so the §2.2 abstraction of continuous plant dynamics is appropriate rather than a gap. *Optional, not required:* a brief note tying one defect to its physical consequence (the stairwell light staying on) would still make the motivation vivid, but it is a presentation nicety, not a scope requirement. **This item is downgraded from a weakness to a non-issue; the technical weaknesses below (W2–W8) are what matter.**

### W2 — The "defect" in the flagship unsound case is one the tool *self-reports*
For `stairs_light` (Discrepancy 2 / §4.3 / §5.1), ESBMC-PLC's own front-end **prints a warning** that "FB/timer outputs on rail→coil paths are not yet modeled" and skips the rung. So the "unsound missed bug" is arguably a **documented, self-announced incompleteness**, not a hidden defect the oracle uncovered. This substantially weakens the "we caught a dangerous soundness bug" narrative for that case: a user is warned. The paper should (a) acknowledge that ESBMC emits this warning and argue why silent-warning-plus-`VERIFICATION SUCCESSFUL` is still unsound-in-effect (a fair argument — the verdict contradicts the warning), and (b) lean more on the **havoc** case (`traffic_light`), which is the genuinely subtle, non-self-reported defect. As written, §1.4 and §5.1 oversell the skip case.

### W3 — The oracle and its "independent" tie-breaker share a ground truth
K-ESBMC's timers/counters are validated *against* MATIEC (§3.2), and MATIEC/OpenPLC is then used as the *independent* tie-breaker for disagreements (§4.1, engine iii). These are the **same C codebase**. If MATIEC itself deviates from IEC 61131-3 (it is a community implementation, not a certified reference), then K-ESBMC and its "independent third witness" are wrong *together*, and the paper's repeated "OpenPLC confirms" carries less weight than "independent" implies. The paper half-acknowledges this ("we take MATIEC's implementations as ground truth") but simultaneously frames OpenPLC as *independent* corroboration (abstract; §4.3; §6 "an independent third witness"). **This is a construct-validity issue that should be stated plainly:** the ground truth is *deployed-runtime behavior*, not the *standard text*, and the standard-conformance claim rests on the (unverified) assumption that MATIEC conforms.

### W4 — RQ4 proves the easy fragment; the interesting constructs are unmechanized
The seven machine-checked lemmas (Table 4) cover exactly the **combinational + latch** fragment — single-scan, near-trivial properties. Every *defect the paper finds is in timers*, which are **not** mechanized (§3.4 boundary paragraph). So the "in part proven" assurance layer does not touch the part of the semantics on which the entire empirical contribution depends. This is disclosed honestly, but it means RQ4's contribution is modest and should not be foregrounded as if it de-risks the timer results. Consider framing RQ4 as "sanity-level mechanization of the base fragment" rather than a headline contribution.

### W5 — External validity: one verifier, 13 programs, generality only asserted
The paper repeatedly claims the oracle is reusable against **any** LD verifier (§6 Generality; §7), but demonstrates it against exactly **one** tool — **ESBMC-PLC, from the authors' own group** (`\cite{DantasCordeiro2026...}`). No differential run against PLCverif, Arcade.PLC, or an SMV/nuXmv flow — the very tools tabulated in Table 1 — even though those are open and would directly substantiate the generality claim. The self-referential setup (auditing your own line's immature front-end) is honest but limits the impact: it reads closer to a **bug report on one prototype** than a general auditing methodology validated across tools. At least one second verifier on the same benchmarks would transform the generality claim from asserted to demonstrated.

### W6 — Table inconsistency: three disagreements vs. two taxonomy rows
Table 3 (`tab:e3`) lists **three** disagreement rows (`stairs_light`, `traffic_light`, `traffic_light (unsafe)`), and the text says "three corroborated discrepancies" (§1.5, §8) and "three disagreements" (§4.3). But the taxonomy Table 5 (`tab:e3tax`) has only **two** rows. Reconcile: either the two `traffic_light` rows are the *same* defect (then say "3 disagreeing program-runs, 2 defect classes, on 2 distinct programs") or they are distinct. As written it is a visible internal inconsistency a reviewer will flag.

### W7 — Bounded input sampling may under-explore deep sequential behavior
§4.1 samples 48 of `2^k` input combinations (when `k` is large), concatenated over 3 sweeps. For sequential controllers whose violations require a *specific multi-scan input sequence* (not just enumerated per-scan assignments), this enumerate-per-scan strategy can miss violations that need correlated inputs across scans. The paper argues a missed violation "would have to evade the entire enumerated input space at every logged scan," but that argument covers *memoryless* violations, not path-dependent ones. State this limitation more precisely.

### W8 — Fault-injection study is thin and partly inert
Acknowledged in §7, but worth restating as a weakness: 2 benchmarks, the **latch operator never fires**, the **timer operator fires once (on dead code)**. So two of the five operators — including the timer operator, the one most relevant to the paper's actual findings — are essentially unexercised. The 27% property-adequacy number is computed over a sample where the most interesting fault classes barely participate. Either broaden the campaign (more latch/timer-heavy benchmarks) or downgrade the claim's prominence.

---

## Suggestions for Revision

1. **Anonymize the manuscript** for TOSEM double-anonymous review (class option, `0.metadata.tex` author block, first-person self-citations, identifying repo/DOI URLs, acknowledgments). Confirm current TOSEM policy on the author-guidelines page. *(The `\acmJournal{TOSEM}` metadata is correct — no change needed; length is not gated at TOSEM.)*
2. **(Optional) Sharpen motivation** (W1, presentation only): a short note tying one defect to a physical outcome (e.g., the stairwell light staying on while the corridor is empty) makes the stakes vivid, but is not required for TOSEM scope.
3. **Rebalance the two case studies** (W2): acknowledge ESBMC's self-warning on `stairs_light`, and promote the `traffic_light` havoc case — the genuinely non-obvious defect — to lead. Argue explicitly why `WARNING + VERIFICATION SUCCESSFUL` is unsound-in-effect.
4. **Add a construct-validity paragraph on the shared ground truth** (W3): state that the reference is deployed-runtime behavior (MATIEC), that the standard-conformance claim is conditional on MATIEC conformance, and that OpenPLC corroboration is "independent of ESBMC" but not "independent of the oracle's validation basis."
5. **Demonstrate generality with a second verifier** (W5): even a small run of PLCverif or Arcade.PLC on 2–3 of the benchmarks would convert the paper's central methodological claim from asserted to evidenced. This is the single highest-impact addition.
6. **Reconcile Tables 3 and 5** (W6) and make the disagreement count unambiguous throughout.
7. **Reframe RQ4** (W4) as base-fragment mechanization, not a de-risking of the timer results; be explicit that the proven fragment and the buggy fragment are disjoint.
8. **Tighten the sampling threat** (W7) to distinguish memoryless from path-dependent violations.
9. **Writing:** the abstract's first sentence has a broken subject/verb structure — "*Automated verifiers … (e.g., the ESBMC-PLC line), lowers LD into a GOTO IR …*" (plural subject, singular verb, dangling clause). Rewrite. Also give a consistent name: the tool is variously `kesbmc` and "K-ESBMC" (title vs. running text) — pick one and define the relationship once.

---

## Questions for the Authors

1. Does ESBMC-PLC emit its "timer not yet modeled" warning on `stairs_light` at the same time it returns `VERIFICATION SUCCESSFUL`? If so, why is this a *silent* soundness defect rather than a *documented* incompleteness with a loud warning?
2. Since K-ESBMC's timers were *ported from* MATIEC and MATIEC is *also* the tie-breaker, what independent evidence do you have that MATIEC itself conforms to the IEC 61131-3 text (as opposed to being the de-facto behavior you've defined conformance to be)?
3. Table 3 shows three disagreeing rows but Table 5 two defect classes — how many *distinct programs* and how many *distinct defects* are you claiming? Please make the count consistent.
4. Your generality claim is central. What prevents running the differential against PLCverif or Arcade.PLC on the same 13 benchmarks, and would you commit to including at least one second verifier?
5. For the bounded differential: can your per-scan input enumeration expose a violation that requires a *specific correlated input sequence across scans* (e.g., a counter that only overflows under a particular ordering), or only memoryless per-scan violations?
6. The `bottle_filling` dead-timer observation (§4.4) implies the benchmark suite's timer coverage is weak. How representative is this suite of real safety-critical LD programs, and does the property-adequacy gap generalize beyond these specific benchmarks?
7. Beyond ESBMC-PLC, which other LD verifiers have you (or could you) run through the differential harness, and what would it take to include one in this paper?

---

## Scores (0–10)

| Dimension | Score | Note |
| --- | --- | --- |
| Novelty | 6 | Method (executable K reference → differential testing of implementations) is established (KEVM, K-C); the *delta* is applying it to a verifier's front-end in the PLC domain, plus the LD extension of K-ST. Solid but incremental. |
| Significance | 6 | The audit-your-verifier framing is valuable; impact is capped by single-tool, self-referential evaluation and the self-reported nature of the flagship defect. |
| Technical Soundness | 7 | Semantics and validation are careful and honestly scoped; the shared-ground-truth (W3) and unmechanized-timer (W4) issues are the main soundness caveats, both partly acknowledged. |
| Evaluation Rigor | 5 | Clean differential and good tie-breaker discipline, but 13 programs / 1 verifier / thin fault-injection / bounded sampling. |
| Reproducibility | 9 | Artifact, container, per-row commands, Zenodo. Exemplary. |
| Related-Work Positioning | 7 | Table 1 and §2.6 are good; generality claimed against tools never actually compared. |
| Writing | 7 | Well-organized and persuasive; some overselling (§1.4/§1.5), abstract grammar, naming inconsistency, table mismatch. |

---

## Simulated Reviewer Reports

### Reviewer A — CPS / Formal-Methods Domain Expert
The K semantics is competently built and the validation-then-use discipline (RQ1 before RQ2/3) is exactly right. My concern is that the mechanized guarantees cover only the fragment where nothing interesting happens, while the timer results — the whole payoff — rest on execution validation against MATIEC, which is also the tie-breaker. The "independent" corroboration is weaker than the prose claims. The `stairs_light` case is a tool that *warns* it doesn't model timers; that is less a discovered soundness bug than a known hole. The `traffic_light` havoc case is the real find. **Recommendation: Major Revision. Confidence: 4/5.**

### Reviewer B — Evaluation-Methodology Expert
Reproducibility is excellent. But the empirical base is narrow: one verifier (the authors' own), 13 programs, and a fault-injection study where two of five operators barely fire. The property-adequacy gap (27%) is a nice observation but is measured on an under-powered sample. The generality claim is asserted, not tested — no second verifier despite Table 1 listing open alternatives. Bounded per-scan input sampling needs a sharper threat statement for path-dependent violations. Add a second verifier and broaden fault injection and this becomes convincing. **Recommendation: Major Revision. Confidence: 4/5.**

### Reviewer C — Associate Editor (TOSEM)
Scope fit is strong: an executable reference semantics used to audit a translation-based verifier is squarely TOSEM material, and the artifact is exemplary. One blocking hygiene item — the manuscript is **not anonymized** for double-anonymous review (author block, first-person self-citations to the tool-under-test's own line, identifying URLs). Beyond that, my editorial concern is *evaluation breadth*: the methodology is sold as general but demonstrated on a single, in-group verifier over 13 programs, and the headline unsound case is one the tool self-reports. I would request a second verifier and a rebalanced case-study emphasis rather than reject. The core idea is genuinely useful to the TOSEM readership. **Recommendation: Major Revision (anonymization gating; generality the key technical ask). Confidence: 4/5.**

---

## Final Editorial Recommendation

**Major Revision** (gated on anonymization; the key technical ask is broader evaluation).

**Rationale:** The central idea — audit a translation-based verifier with an executable, standard-faithful reference semantics — is sound, well-executed at small scale, backed by an exemplary artifact, and a **strong scope fit for TOSEM**. It is held back from acceptance by (1) one blocking submission-hygiene issue (anonymization), (2) a single-tool, partly self-referential evaluation whose flagship "unsound" defect is self-reported by the tool, and (3) an assurance story whose proven fragment is disjoint from its buggy fragment. None is fatal; all are addressable. The highest-leverage revisions are: add a second verifier (W5), rebalance the case studies toward the genuinely subtle havoc defect (W2), and add the shared-ground-truth construct-validity caveat (W3).

**Acceptance probability after a strong revision:** good at TOSEM — the venue fit is right and the artifact is a real asset; the gap to acceptance is evaluation breadth and honest reframing, not a structural flaw.

---

## Top revisions, prioritized

1. Anonymize for double-anonymous review — class option, author block, first-person self-cites, identifying repo/DOI URLs. Confirm current TOSEM policy. *(gating)*
2. Add a second verifier (PLCverif / Arcade.PLC) on ≥ 3 benchmarks to substantiate the generality claim. *(highest technical impact)*
3. Acknowledge ESBMC's self-warning on `stairs_light`; promote the `traffic_light` havoc case as the lead result.
4. Add a construct-validity paragraph on the shared MATIEC ground truth (W3).
5. Reframe RQ4 as base-fragment mechanization, disjoint from the timer results (W4).
6. Reconcile Tables 3 and 5 and make the disagreement count consistent (W6).
7. Tighten the bounded-sampling threat to distinguish memoryless vs. path-dependent violations (W7).
8. Broaden or downgrade the fault-injection study (latch/timer operators are under-exercised) (W8).
9. Fix the abstract's opening sentence (broken subject/verb) and settle the `kesbmc` vs. K-ESBMC naming.
10. *(Optional)* Add a one-line physical-consequence note for the stairwell-light defect to sharpen motivation — presentation only, not required for TOSEM.
