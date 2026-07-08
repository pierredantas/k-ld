# K-ESBMC — An Executable Formal Semantics of IEC 61131-3 Ladder Diagram

**K-ESBMC** is an executable formal semantics of the IEC 61131-3 **Ladder Diagram (LD)**
language, written in the [K framework](https://kframework.org). It extends **K-ST**
(the K semantics of Structured Text) to the graphical LD language and its function
blocks, and serves as an **independent reference oracle** for validating the LD→GOTO
translation used by LD verifiers such as ESBMC-PLC.

From a single definition, K yields both an **interpreter** (`krun`, used to execute
diagrams scan by scan) and a **deductive verifier** (`kprove`, used to machine-check
construct-correctness lemmas).

This repository is the **software artifact**. The paper is maintained separately.

## What is here

```
k-esbmc/
├── ld-syntax.k, ld.k     # the K-ESBMC semantics: contacts, coils/latches, the scan
│                         #   cycle, TON/TOF/TP, CTU/CTD, R_TRIG/F_TRIG
├── tests/, Makefile      # per-construct conformance tests (make d-test-*)
├── Dockerfile            # builds the K toolchain image (no host install needed)
├── validation/           # RQ1: OpenPLC/MATIEC scan-for-scan fidelity harness
│   ├── run.sh            #   extract MATIEC reference FBs, execute, compare to K-ESBMC
│   └── matiec_ref.c
├── rung6/                # the differential study (K-ESBMC as oracle vs a verifier)
│   ├── plcopen2kld.py    #   PLCopen XML (simple <rung> format) → K-ESBMC DSL
│   ├── graphical2kld.py  #   PLCopen XML (graphical netlist) → K-ESBMC DSL
│   ├── differential.py   #   drive input traces, check each property per scan
│   ├── run_all.py        #   three-engine driver → results.md
│   ├── results.md        #   recorded results (13 programs)
│   └── FINDINGS.md       #   the discrepancies, analysed
└── proof/                # RQ4: kprove construct-correctness lemmas
    ├── verification.k    #   7 machine-checked combinational/latch lemmas
    └── timer-spec.k      #   inductive timer lemma (open; obstacle documented)
```

## Requirements

- **Docker.** The K toolchain runs inside a container built from `k-esbmc/Dockerfile`,
  so no host K/LaTeX install is needed. On Apple Silicon the amd64 image runs under
  emulation.
- For the OpenPLC fidelity check, the `tuttas/openplc_v3` image is pulled
  automatically by `validation/run.sh`.
- Reproducing the **full** differential additionally needs **ESBMC v8.3.0** and the
  public ESBMC-PLC **benchmark suite** (both external to this artifact). The K-ESBMC
  side of every comparison, and the recorded outcomes in `rung6/results.md`, are
  included here.

## Quick start

```bash
cd k-esbmc
make d-build          # build the K image and kompile the semantics
make d-test-ton       # run a conformance test (on-delay timer)
```

### Reproduce the results

**RQ1 — fidelity vs OpenPLC/MATIEC** (self-contained; Docker only):
```bash
cd k-esbmc
make d-test-and d-test-latch d-test-ton d-test-tof d-test-tp d-test-ctu d-test-ctd
bash validation/run.sh        # executes the MATIEC reference FBs and prints their
                              # traces; compare against the K-ESBMC traces above
```

**RQ2/RQ3 — the differential** (K-ESBMC side; the ESBMC side needs the external tool):
```bash
cd k-esbmc/rung6
python3 graphical2kld.py <bench>.ld gen/<bench>.json > gen/<bench>.ld   # translate
python3 differential.py gen/<bench>.ld gen/<bench>.json <props>.yaml    # K-ESBMC verdict
# run_all.py drives all benchmarks through both engines -> results.md
cat results.md FINDINGS.md
```

**RQ4 — machine-checked lemmas**:
```bash
cd k-esbmc
make d-prove          # kprove the 7 combinational/latch construct lemmas -> #Top
```

## Results at a glance

- **Fidelity (RQ1).** K-ESBMC reproduces the OpenPLC/MATIEC done-bit trace of every
  function block (TON/TOF/TP, CTU/CTD) exactly, scan for scan.
- **Differential (RQ2/RQ3).** Over 13 programs, K-ESBMC and ESBMC agree on 10; the three
  disagreements are all genuine ESBMC defects (corroborated by OpenPLC), splitting
  into two timer-translation failure modes — an unsound *skip* (a real violation
  missed) and an imprecise *havoc* (impossible counterexamples). See
  `rung6/FINDINGS.md`.
- **Proofs (RQ4).** The combinational and latch fragment is machine-checked in
  `kprove` (7 lemmas). The inductive timer/counter lemmas are open; the obstacle is
  documented in `proof/timer-spec.k`.

## Using K-ESBMC on your own programs

K-ESBMC is an independent oracle: you can run it on any IEC 61131-3 LD program and diff
its verdict against **any** verifier (not just ESBMC). For a PLCopen XML diagram
`mydiagram.ld` and a properties file `myprops.yaml` (using the `invariant` /
`absence` / `mutual_exclusion` kinds, as in the benchmarks):

```bash
cd k-esbmc/rung6
# 1. Translate the diagram into K-ESBMC DSL. Pick the frontend by format:
#    graphical netlist -> graphical2kld.py ; linear <rung> format -> plcopen2kld.py
python3 graphical2kld.py mydiagram.ld gen/mydiagram.json > gen/mydiagram.ld

# 2. Run K-ESBMC as the oracle: it executes the diagram over input traces and checks
#    each property on every scan, returning SAFE / VIOLATED(+witness) per property.
python3 differential.py gen/mydiagram.ld gen/mydiagram.json myprops.yaml

# 3. (optional) Compare against your verifier's verdict; use OpenPLC (validation/)
#    as an independent tie-breaker on any disagreement.
```

**Scope.** This works out of the box for the Boolean-signal fragment with the
standard function blocks: contacts, coils/latches, `TON`/`TOF`/`TP`, `CTU`/`CTD`,
`R_TRIG`/`F_TRIG`, in both diagram formats. Outside it — non-Boolean data
(integer/analog arithmetic), non-standard or vendor function blocks, or FBD/SFC
bodies — the translator flags the unsupported construct rather than producing a wrong
answer, and support is added rule-by-rule in `ld.k` (plus a case in the relevant
`*2kld.py` frontend). This is a research artifact, not a hardened product.

## License

MIT (see `.zenodo.json`).
