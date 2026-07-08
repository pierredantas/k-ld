# LaTeX pass — fold WP1a (MATIEC-C+CBMC) + WP1b (NuSMV) into the paper

Ready-to-paste LaTeX for the `ACM/` sources. **Scope guardrail (important for honesty):**
WP1a/WP1b were executed on the **controlled timer probe** (`Btn→TON→Light`), not re-run
across all 13 benchmarks. Every edit below therefore frames the two extra engines as
independent corroboration of the **timer mechanism** underlying the disagreements (which is
exactly what that probe isolates) — *not* as a 13-program multi-engine sweep. Keep that
framing when you apply it.

Existing bib keys reused: `Clarke2004cbmc` (CBMC), and `\gls{cbmc}`/`\gls{bmc}`/`\gls{matiec}`
acronyms already exist. One new bib entry (NuSMV) is in §6 below.

---

## Edit 1 — `_sec_e3.tex`, §4.3 (RQ3) opening sentence

**Find:**
```latex
The three disagreements all involve timer function blocks, and OpenPLC confirms \kesbmc{} in every case. They expose two \emph{opposite} defects in \gls{esbmc}'s incomplete timer translation (Table~\ref{tab:e3tax}).
```
**Replace with:**
```latex
The three disagreements all involve timer function blocks, and OpenPLC confirms \kesbmc{} in every case; on the controlled probe below, two further independent verification engines corroborate \kesbmc{} as well (Table~\ref{tab:e3:multiengine}). They expose two \emph{opposite} defects in \gls{esbmc}'s incomplete timer translation (Table~\ref{tab:e3tax}).
```

---

## Edit 2 — `_sec_e3.tex`, §4.3: new paragraph + table, immediately AFTER the "A controlled probe" paragraph

The controlled-probe paragraph ends with:
```latex
\gls{esbmc} therefore leaves the timer output \emph{unconstrained} (havoc), an over-approximation that manufactures false alarms.
```
**Insert directly after it:**
```latex
\paragraph{Independent cross-engine corroboration.} The probe's verdict does not rest on \kesbmc{} alone. We re-check the invariant \code{A} with two engines that share no code with either \gls{esbmc} or \kesbmc{} and that use different decision procedures: the diagram compiled to C by \gls{matiec} and discharged by \gls{cbmc}~\cite{Clarke2004cbmc} -- a distinct SAT-based \gls{bmc} back-end -- and NuSMV~\cite{Cimatti2002nusmv}, whose BDD-based symbolic model checking is unrelated to bounded unrolling. Both report \code{A} \textsc{safe}, and NuSMV's proof is \emph{unbounded} -- a fixpoint over all reachable states, not merely up to a horizon. Together with the OpenPLC runtime, four independent accounts thus agree against \gls{esbmc} (Table~\ref{tab:e3:multiengine}), isolating its timer \emph{havoc} as the sole cause of the false alarm; because these engines differ in both front-end and decision procedure, the disagreement can be neither an artifact of \kesbmc{}'s modeling choices nor of \gls{bmc} in particular. We report these corroborations on the mechanism-isolating probe; the differential harness admits the same engines on the full suite.

\begin{table}[t]
    \centering
    \caption{Controlled timer probe \code{Btn}$\to$\code{TON}$\to$\code{Light}, invariant \code{A}: ``\code{!Light || Btn}''. Four independent accounts -- an executable oracle, two verifiers with unrelated decision procedures, and the deployed runtime -- agree the property holds under a faithful timer; only \gls{esbmc}, which \emph{havocs} the timer output, reports a violation. NuSMV's BDD proof is unbounded.}
    \label{tab:e3:multiengine}
    \small
    \begin{tabular}{@{}llc@{}}
        \toprule
        Engine & Method & \code{A} \\
        \midrule
        \gls{esbmc}-\gls{plc}          & SMT-\gls{bmc} (havocs timer)   & \textsc{violated} \\
        \kesbmc{}                       & executable reachability        & \textsc{safe} \\
        \gls{matiec}$\to$C\,$+$\,\gls{cbmc} & SAT-\gls{bmc}              & \textsc{safe} \\
        NuSMV                           & BDD symbolic (unbounded)       & \textsc{safe} \\
        OpenPLC/\gls{matiec}            & concrete execution             & \textsc{safe} \\
        \bottomrule
    \end{tabular}
\end{table}
```

---

## Edit 3 — `_sec_e3.tex`, §4.5 Threats, item (i) bounded-horizon

**Find** (end of the (i) construct-validity discussion):
```latex
Reported \textsc{safe} verdicts should nonetheless be read as safe-up-to-horizon, matching \gls{esbmc}'s own bounded model.
```
**Replace with:**
```latex
Reported \textsc{safe} verdicts should nonetheless be read as safe-up-to-horizon, matching \gls{esbmc}'s own bounded model -- with one exception at the heart of the disagreements: on the controlled timer probe (\S\ref{sec:e3:rq3}) NuSMV discharges invariant \code{A} by an \emph{unbounded} BDD fixpoint, so there the \textsc{safe} verdict holds over all reachable states, not only to the horizon.
```

---

## Edit 4 — `_sec_e3.tex`, §4.1 "Reproducibility" paragraph (optional but recommended)

**Append one sentence** to the Reproducibility paragraph:
```latex
The driver also admits auxiliary corroboration engines -- the diagram compiled to C by \gls{matiec} and checked with \gls{cbmc}, and NuSMV on a BDD encoding -- used in \S\ref{sec:e3:rq3} to cross-check the timer mechanism with decision procedures independent of \kesbmc{}.
```

---

## Edit 5 — `_sec_text.tex`, §1.6 Contributions, item 3 (optional)

**Find:**
```latex
We report broad agreement and three corroborated discrepancies, and classify them into \gls{esbmc}'s two timer-translation failure modes -- unsound \emph{skip} (missed bugs) and imprecise \emph{havoc} (false alarms).
```
**Replace with:**
```latex
We report broad agreement and three discrepancies -- each corroborated by the OpenPLC runtime and, on the timer mechanism they share, by two further independent verification engines (\gls{matiec}$\to$C$+$\gls{cbmc} and NuSMV) -- and classify them into \gls{esbmc}'s two timer-translation failure modes: unsound \emph{skip} (missed bugs) and imprecise \emph{havoc} (false alarms).
```

---

## Edit 6 — `0.sample-base.bib`, add the NuSMV entry

Place near the existing `Cavada2014` (nuXmv) entry:
```bibtex
@inproceedings{Cimatti2002nusmv,
  author    = {Cimatti, Alessandro and Clarke, Edmund and Giunchiglia, Enrico and Giunchiglia, Fausto and Pistore, Marco and Roveri, Marco and Sebastiani, Roberto and Tacchella, Armando},
  title     = {{NuSMV} 2: An {OpenSource} Tool for Symbolic Model Checking},
  booktitle = {Computer Aided Verification (CAV 2002)},
  series    = {Lecture Notes in Computer Science},
  volume    = {2404},
  pages     = {359--364},
  year      = {2002},
  publisher = {Springer},
  doi       = {10.1007/3-540-45657-0_29},
}
```

---

## Edit 7 — Abstract (`0.metadata.tex`), optional light touch

**Find:**
```latex
every \emph{disagreement} is a genuine \gls{esbmc} defect that \kesbmc{} exposes and OpenPLC confirms
```
**Replace with:**
```latex
every \emph{disagreement} is a genuine \gls{esbmc} defect that \kesbmc{} exposes, that OpenPLC confirms, and that two further independent verification engines corroborate
```

---

## Edit 8 — `_sec_text.tex`, §5 Related Work: PLCverif/Arcade.PLC footnote

**Find:**
```latex
it is the reference oracle against which such a translation can be scrutinized, and we apply it to \esbmcplc{}.
```
**Replace with:**
```latex
it is the reference oracle against which such a translation can be scrutinized, and we apply it to \esbmcplc{}.\footnote{We apply the differential to \esbmcplc{} rather than to these other tools because none can ingest our PLCopen~XML \gls{ld} benchmarks without a further trusted translation: PLCverif's only \gls{plc} front-end targets Siemens Step7 (\acrshort{scl}/STL), and Arcade.PLC is no longer distributed. We instead corroborate the disagreements with verification engines whose decision procedures are independent of \kesbmc{} (\S\ref{sec:e3:rq3}).}
```

---

## Application order / checklist
1. Add the bib entry (Edit 6) first so the `\cite{Cimatti2002nusmv}` in Edit 2 resolves.
2. Apply Edits 1–3 (the substantive RQ3 + threats changes).
3. Apply Edits 4, 5, 7 if you want the lighter touches in setup / contributions / abstract.
4. Recompile; check `Table~\ref{tab:e3:multiengine}` renders and the two new `\cite`/`\ref`
   resolve (no `??`).

## What is claimed vs. what was run (for your own tracking)
- **Ran, real tools:** MATIEC `iec2c`→C + CBMC 6.10 and NuSMV 2.6.0, both on the
  `Btn→TON→Light` probe — faithful ⇒ `A` safe (NuSMV unbounded), havoc ⇒ `A` violated.
  Artifacts: `k-esbmc/rung8_wp1a/matiec_cbmc/`, `k-esbmc/rung9_wp1b/`.
- **Not run (do not imply):** MATIEC-C+CBMC / NuSMV across all 13 benchmarks. The text says
  "on the controlled probe" and "the harness admits the same engines on the full suite" —
  keep that scoping.
- **PLCverif/Arcade.PLC:** deliberately not claimed as used; if a reviewer asks about other
  verifiers, the honest answer is in `k-esbmc/rung9_wp1b/PLCVERIF.md` (PLCverif is Siemens-only,
  Arcade.PLC defunct) — consider a one-line footnote in Related Work if you want it on record.
