# K-ESBMC — Executable Formal Semantics for IEC 61131-3 Ladder Diagram

Machine-checked LD semantics in the **K framework**, extending **K-ST** (Wang et al., TSE 2023).
Serves as the reference oracle to validate the ESBMC-PLC `LD → GOTO IR` translation.

**Ground truth for conformance (E1/E2):** OpenPLC v3.

## Build ladder (low → high complexity)

| Rung | Work | Status |
|------|------|--------|
| 0 | Install K; build & run K-ST examples | ⬅️ **current** |
| 1 | Fragment scope + LD syntax (`ld-syntax.k`) | draft written |
| 2 | Combinational core: XIC/XIO + OTE, one scan (`ld.k`) | ✅ done & green |
| 3 | Scan-cycle model + OTL/OTU latches (retention) | ✅ done & green |
| 4 | Timers TON/TOF/TP (Δt time model) | ✅ done & green |
| 5 | Counters CTU/CTD (edge + reset dominance) | ✅ done & green |
| 6 | E3 differential harness vs ESBMC (18 benchmarks) | todo |
| 7 | E4 mutation sensitivity | todo |
| 8 | E5 mechanized construct lemmas (`kprove`) | 🟡 started — 7 lemmas proved (contacts, OTE, OTL/OTU set+retain); timers/counters (induction) next |

## Rung 0 — toolchain

There is **no macOS/arm64 K binary** (releases ship only Ubuntu `.deb` + source),
and the official Nix installer needs an interactive admin prompt. So on macOS we
run K **inside Docker** (`Dockerfile` builds the K image from the Ubuntu Noble
`.deb`, amd64 under emulation). No host install, no sudo, no Nix — and the same
image is the paper's artifact-evaluation container.

Start Docker Desktop, then:

```
make image        # build the K toolchain image (first time: several minutes)
make d-build      # kompile ld.k inside the container
make d-test-and   # I0=I1=true       -> expect Q0 |-> true
make d-test-and-neg  # I0=true,I1=false -> expect Q0 |-> false
make d-shell      # interactive shell in the K image (for poking with krun)
```

OpenPLC v3 ground truth (separate container):

```
docker run -d -p 8080:8080 --name openplc thiagoralves/openplc_v3
# editor + runtime at http://localhost:8080  (default login openplc/openplc)
```

> If you ever install K natively (Nix/kup), the plain `make build` / `make test-*`
> targets use host K directly; `make check` reports whether it's on PATH.

> `ld.k` is a **first, un-kompiled draft** (Rung 2). Expect to iterate on
> strictness/heating once `kompile` is in the loop; the *intent* of each rule
> (contact lookup, series=AND, parallel=OR, OTE writes the coil) is the stable part.

## Ground-truth validation (E1/E2) vs OpenPLC

`validation/` cross-checks K-ESBMC against OpenPLC's actual engine. `run.sh` extracts
MATIEC's reference function-block C (`iec_std_FB.h`, the exact code OpenPLC runs)
from the container, compiles `matiec_ref.c` against it, and executes the same input
traces K-ESBMC uses. All five FBs (TON/TOF/TP, CTU/CTD) match K-ESBMC scan-for-scan.

```
bash validation/run.sh      # requires Docker
```

This is what caught (and fixed) the timer off-by-one and CTU saturation: K-ESBMC's
timers are now a direct port of MATIEC's 3-valued STATE machine, so they fire
PT/Δt scans after the trigger edge exactly like OpenPLC/IEC.

## Files

- `ld-syntax.k` — abstract syntax = the covered fragment F
- `ld.k` — full semantics: contacts, coils/latches, scan cycle, timers, counters
- `tests/*.ld` + `Makefile` — per-construct conformance tests (`make d-test-*`)
- `validation/` — OpenPLC/MATIEC ground-truth harness (`run.sh`, `matiec_ref.c`)
