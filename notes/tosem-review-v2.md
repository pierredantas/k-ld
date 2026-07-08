# ACM TOSEM Review (v2, full) — K-ESBMC

**Manuscript:** *K-ESBMC: An Executable Formal Semantics of IEC 61131-3 Ladder Diagram for Validating Verifier Translations*
**Venue:** ACM TOSEM · **Rubric:** `tcps-reviewer` phases adapted to TOSEM (CPS scope-gate replaced by SE-methodology fit)
**Reviewed state:** current `ACM/` after WP1a/WP1b/WP2/WP3 edits + K-ESBMC rename
**Supersedes:** `tosem-review.md` (v1), written pre-edits.

---

## What changed since v1 (and what it fixed)

| v1 weakness | Status in v2 |
| --- | --- |
| W5 — single verifier | **Partly fixed.** Multi-engine corroboration (K-ESBMC, MATIEC-C+CBMC, NuSMV, OpenPLC) — *but only on the controlled probe* (see M1). |
| W5b — 13 programs, incidental coverage | **Fixed.** Synthetic family (corpus 28) + coverage matrix; §4.1, §4.4. |
| W7 — bounded horizon | **Partly fixed.** NuSMV's unbounded BDD proof on the probe; the 13-program differential is still bounded. |
| W8 — inert fault operators | **Fixed.** WP3 family campaign; LR/TK now fire (Table `tab:e3:family`). |
| W2 — self-reported skip defect | **Improved disclosure** (§4.3 states the warning) but a new internal inconsistency appeared (see M3). |
| W1 — TOSEM scope | **Non-issue** (correct venue). |

Net: the evaluation is materially stronger. But the additions introduced two new substantive issues (M1, M2) and the gating/consistency items from v1 persist.

---

## Gating (TOSEM)

| Gate | Status |
| --- | --- |
| Scope fit (SE methodology) | **Strong** — program semantics, translation validation, differential/mutation testing. |
| **Double-anonymous** | ❌ **FAIL (blocking).** `\documentclass[acmsmall, review]`; author block with names/emails/ORCIDs (`0.metadata.tex`); first-person self-citations to the ESBMC-PLC line. TOSEM is double-anonymous — must anonymize. *(Unchanged from v1.)* |
| Journal metadata | ✅ `\acmJournal{TOSEM}` correct. |
| Format / length | ✅ `acmsmall`; TOSEM has no hard page cap (the paper grew with the new table + paragraphs — still fine, but watch density). |

---

## Scores (/10) — v2

| Dimension | v1 | v2 | Note |
| --- | --- | --- | --- |
| Novelty | 6 | 6 | Method (executable K reference → differential testing) established; PLC-domain application + LD extension of K-ST is the delta. |
| Significance | 6 | 7 | Multi-engine corroboration + expanded evaluation raise it. |
| Technical soundness | 7 | 7 | Careful and honest; the "four independent accounts" framing over-reaches (M2). |
| Evaluation rigor | 5 | 7 | WP2/WP3 + multi-engine; capped by probe-only breadth (M1) and single verifier on the 13-suite. |
| Reproducibility | 9 | 8 | Still exemplary; −1 until the family campaign is confirmed under `krun` (M4). |
| Positioning | 7 | 7 | Good; nuXmv mentioned but `Cavada2014` uncited (m3). |
| Writing | 7 | 7 | Strong; abstract grammar + one intro/results inconsistency persist. |

---

## Major issues

### M1 — Multi-engine corroboration is demonstrated on ONE minimal program, not the suite
`tab:e3:multiengine` (the four-engine agreement) is entirely the `Btn→TON→Light` probe. The actual 13-program differential (Table `tab:e3`, RQ2/RQ3) is still **K-ESBMC vs ESBMC-PLC**, with OpenPLC as tie-breaker. So the headline "four independent accounts agree against ESBMC" substantiates the *mechanism* behind Discrepancy 1 (havoc), not the benchmark verdicts. The paper is honest ("we report these corroborations on the mechanism-isolating probe; the harness admits the same engines on the full suite"), but a reviewer will immediately ask **why the multi-engine check wasn't run on the full suite** — especially the two decisive programs (`traffic_light`, `stairs_light`). Running MATIEC-C+CBMC and NuSMV on those two would convert "mechanism corroborated" into "verdicts corroborated" and cost little. **Highest-value revision.**

### M2 — "Four independent accounts" overstates independence (the shared-ground-truth issue, amplified)
The four are presented as independent, but three share a semantic basis:
- **OpenPLC** and **MATIEC-C+CBMC** both execute *MATIEC*'s function-block semantics;
- **K-ESBMC** was *validated against MATIEC* (§3.2, RQ1);
- **NuSMV** runs on an SMV model *the authors wrote* to encode the same faithful timer.

So the genuinely independent bases are roughly **two** — the MATIEC family and the authors' faithful-timer encoding — not four, and ESBMC is the lone tool with an independent *front-end*. The claim "share no code with either ESBMC or K-ESBMC" is true at the tool level but misleading at the semantic level: CBMC/NuSMV differ in *decision procedure*, not in the *timer semantics* being checked. **The text must state this plainly** — the corroboration rules out a BMC-specific or K-ESBMC-modeling artifact, but does not add a fully independent account of the standard beyond MATIEC. This is the same W3 concern v1 raised (K-ESBMC and its "independent" tie-breaker share MATIEC); the multi-engine addition makes precise wording more important, not less.

### M3 — Intro says the skip is "silent"; §4.3 says the tool warns
- §1.4: "a safety property verified away by a front-end that **silently** dropped the timer."
- §4.3 (Discrepancy 2): "Its front-end **warns** that 'FB/timer outputs … are not yet modeled' and skips the timer path."

These contradict. If ESBMC emits a warning, "silently" is wrong, and the "unsound" framing needs the sharper argument (which the paper can make): *a warning does not lift the `VERIFICATION SUCCESSFUL` verdict, so a user acting on the verdict is misled*. Reconcile §1.4 with §4.3 and drop "silently" for the stairs case.

### M4 — Confirm the family-campaign numbers under `krun`
`tab:e3:family` (87 mutants; 73 behavioral; 32 = 44%; LR 4× / TK 5×) must be produced by the canonical oracle. In the artifact these were computed by a validated secondary executor (reproduces the RQ1 Table 2 traces and NuSMV labels), but the paper states them as K-ESBMC results. Run `rung6/differential.py` over `rung10_wp2/family/` under K and confirm the three integers and "44%" before submission; the qualitative claims survive small shifts.

### M5 — RQ4's mechanized guarantee still excludes the constructs where the bugs live
The seven `kprove` lemmas cover combinational + latch; **every reported defect is in timers**, which remain unmechanized (§3.4). Honestly disclosed, but it means the "in part proven" assurance layer does not touch the timer semantics that carry the whole result. Keep RQ4 scoped as base-fragment sanity, not as de-risking the timer findings. *(Unchanged from v1.)*

---

## Minor issues

- **m1 — Table `tab:e3` (3 disagreement rows) vs `tab:e3tax` (2 rows).** The two `traffic_light` rows collapse to one defect in the taxonomy; text says "three disagreements." State it once: *3 disagreeing runs, 2 defect classes, on 2 distinct programs.* *(Persists from v1.)*
- **m2 — Abstract opening is ungrammatical.** "Automated verifiers … (e.g., the ESBMC-PLC line), **lowers** LD into a GOTO IR …" — plural subject, singular verb, dangling clause. Rewrite. *(Persists from v1.)*
- **m3 — `Cavada2014` (nuXmv) uncited** though Related Work names "SMV/nuXmv-based flows." Add `\cite{Cavada2014}` there (it's already in the `.bib`).
- **m4 — Single verifier for the 13-program differential.** ESBMC-PLC is the authors' own line; §threats(iv) acknowledges "one verifier." The reusability claim would land harder with even one third-party verifier (PLCverif can't ingest PLCopen LD — worth a one-line footnote, already drafted in `PLCVERIF.md`).

## Fixed / clean (verified mechanically)
- No dangling `\cite` or `\ref`; new `tab:e3:family` / `tab:e3:multiengine` labels + refs resolve; `Cimatti2002nusmv` cited and in `.bib`.
- No leftover placeholders (`\TOINSERT` defined but unused).
- Orphan `fig_kld_overview.tex` removed (delete in Overleaf too).

---

## Claims & evidence audit (key claims)

| Claim | Support | Comment |
| --- | --- | --- |
| Every disagreement is a genuine ESBMC defect | **Strong** | OpenPLC tie-breaker + structural, preset-independent arguments; solid. |
| Two opposite timer failure modes (skip/havoc) | **Strong** | Well-argued; the taxonomy is the paper's best contribution. |
| Four independent engines corroborate | **Overstated** | See M2 — independence is ~2 bases, and only on the probe (M1). |
| Property-adequacy gap (27% / 44%) | **Strong→pending** | Compelling finding; confirm 44% under `krun` (M4). |
| K-ESBMC is a reusable oracle for *any* verifier | **Partial** | Demonstrated on one verifier; NuSMV/CBMC are engines, not independent LD front-ends (M1/M2). |
| Combinational/latch fragment machine-checked | **Strong** | 7 `kprove` lemmas; scope honest (M5). |

---

## Simulated reviewers

**Reviewer A — Formal methods / semantics.** The K semantics and the validate-then-use discipline are sound, and the multi-engine + unbounded-NuSMV additions are welcome. But the "four independent accounts" claim is looser than it reads: three share MATIEC or the authors' own timer encoding, and it's all on one probe. Tighten the independence wording and run the two decisive benchmarks through CBMC/NuSMV. RQ4 still proves only the easy fragment. **Major Revision, confidence 4/5.**

**Reviewer B — Empirical SE / evaluation.** The corpus growth (28), coverage matrix, and the fault-injection campaign with all operators firing substantially answer my v1 concerns; the property-adequacy result is genuinely interesting. Two asks: (a) confirm the family numbers under the canonical oracle, and (b) push the multi-engine comparison past the single probe. Reproducibility is excellent. **Major→Minor Revision, confidence 4/5.**

**Reviewer C — Associate Editor (TOSEM).** Scope fit is strong and the artifact is a real asset. Blocking: the manuscript is **not anonymized** for double-anonymous review. Beyond that, the contribution is solid and the revisions are framing/consistency, not structural. Fix anonymization, the independence over-claim, and the intro/results inconsistency, and this is in good shape. **Major Revision (anonymization gating), confidence 4/5.**

---

## Final recommendation

**Major Revision** — but a healthy one; most items are wording/consistency/confirmation, not new science.

Blocking/high-value, in order:
1. **Anonymize** for double-anonymous review (gating).
2. **M2** — correct the "four independent accounts" independence framing.
3. **M1** — run the multi-engine check on `traffic_light` + `stairs_light` (converts mechanism → verdict corroboration; cheap, high impact).
4. **M3** — reconcile "silently" (§1.4) vs "warns" (§4.3).
5. **M4** — confirm `tab:e3:family` under `krun`.
6. Minors: m1 (table counts), m2 (abstract grammar), m3 (`Cavada2014` cite).

**Acceptance probability after a solid revision: good at TOSEM.** The venue fit is right, the artifact is strong, and the evaluation now claims the breadth it earned. The gap to acceptance is honest framing + anonymization, not missing work.

---

## Publication-readiness checklist
| Item | Status |
| --- | --- |
| TOSEM scope | ✅ Strong |
| Double-anonymized | ❌ blocking |
| Clear novel contribution | ✅ (incremental-but-solid) |
| Technically sound | ✅ (fix M2 framing) |
| Evaluation breadth | ◑ (M1: multi-engine only on probe) |
| Reproducible | ✅ (confirm M4 under krun) |
| Honest limitations | ✅ (RQ4 scope, threats) |
| Related work fair/correct | ✅ (add `Cavada2014`) |
| CCS + ACM ref format | ✅ |
| LaTeX/bib consistency | ✅ (verified) |
