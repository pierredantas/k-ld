# Reviewing the ESBMC-Arduino Artifact

This artifact reproduces every result in the paper. It is self-contained: two scripts install
the tools and regenerate the claims. Read time: 2 min. Run time: ~30–50 min (mostly a one-time
ESBMC build). Verdicts (SAFE/UNSAFE) are deterministic; only wall-clock times vary.

---

## 0. Environment (please read first)

- **Required: x86_64 (amd64) Linux — Ubuntu 22.04 recommended.** `sudo` + internet access.
- ~6 GB free disk, ≥4 GB RAM.
- **Why x86_64 Linux:** the verifier (ESBMC) builds against an x86_64-Linux LLVM toolchain that it
  downloads automatically. **macOS and arm64 cannot build it** — see *"If you only have a Mac /
  arm64"* at the bottom for free x86_64 alternatives.

---

## 1. Download from Zenodo

From the anonymized Zenodo record (concept DOI: `10.5281/zenodo.21014209`,
https://doi.org/10.5281/zenodo.21014209 — always resolves to the latest version), download:

- `esbmc-arduino-artifact.tar.gz`  (the artifact)
- `SHA256SUMS`                      (integrity)

## 2. Verify integrity and extract

```bash
sha256sum -c SHA256SUMS            # expect: esbmc-arduino-artifact.tar.gz: OK
tar xzf esbmc-arduino-artifact.tar.gz
cd artifact
```

## 3. One-time setup (~20–40 min)

```bash
bash setup.sh
```
Installs **CBMC 6.10.0**, **Frama-C 32.1**, **MATIEC**, and **builds the patched ESBMC** (the HAL
annotator) from the bundled source. It writes `env.sh` (tool paths), which the next step uses.
The Frama-C/opam step and the ESBMC build are the slow parts; everything is pinned.

## 4. Reproduce the results

```bash
bash reproduce.sh --smoke     # quick sanity check (~minutes)
bash reproduce.sh --full      # all claims; writes ./results/
```
`reproduce.sh` prints a claim-by-claim summary as it runs.

## 5. Check against the claims

Open **`CLAIMS.md`** — it maps every paper claim to its command and expected output. The headline
checks:

| Claim | Where | Expected |
|-------|-------|----------|
| Keystone **54→0** | `results/keystone.csv` | naive: 54 UNSAFE / HAL: **0** UNSAFE, 32 SAFE preserved |
| Cross-tool (CBMC + Frama-C) | `results/baseline.txt` | phantom reproduced; bound needs manual `assume`; genuine defect width-dependent |
| Real-corpus 54/54 | `results/real_corpus.csv` | CBMC naive 54 FAIL → with bound 54 SAFE |
| Controlled matrix | `results/matrix.csv` | `*_bug` UNSAFE@16-bit / SAFE@32-bit; `*_ok` always SAFE (20/20) |

If those match, the artifact has reproduced the paper.

---

## If you only have a Mac / arm64 machine

ESBMC cannot be built on macOS or arm64. Use any free x86_64 Linux instead — pick one:

- **GitHub Codespaces** (free, x86_64 Ubuntu): create a Codespace, drag in the tarball, then run
  steps 2–4 in its terminal. Easiest.
- **amd64 container on your Mac** (Docker Desktop):
  ```bash
  docker run --platform linux/amd64 -it -v "$PWD:/w" -w /w ubuntu:22.04 bash
  apt-get update && apt-get install -y sudo   # then run steps 2–4 inside
  ```
  Correct environment, but the ESBMC build runs under emulation (slow).
- **Any x86_64 cloud VM** (e.g., a small Ubuntu 22.04 instance).

---

## Notes & troubleshooting

- **Determinism:** verdicts are stable across hosts; times vary.
- **The 91 UNKNOWN** in the keystone are an intentional, documented `k`-induction completeness limit
  (paper §Threats), not failures — the soundness result (no false alarms) holds regardless.
- **`malicious_*` programs** contain a non-terminating logic-bomb loop; the cross-tool step isolates
  the *overflow* property (orthogonal to that loop), as documented in `experiments/baseline/RESULTS.md`.
- **CBMC version:** pinned to 6.10.0; verdicts are stable across CBMC 6.x if your distro differs.
- `setup.sh` can be re-run; it skips tools already installed/built.
- Full tool/version pinning and provenance: `CLAIMS.md`, `corpus/PROVENANCE.md`, `build/hal-annotator.patch`.
