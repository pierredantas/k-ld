# WP1a executed with the real toolchain — results

The WP1a mechanism (an independent MATIEC-C + CBMC verification path) was run
**end-to-end with real tools**, no Docker: MATIEC's `iec2c` compiled from source
(`thiagoralves/matiec`, the OpenPLC fork) and CBMC 6.10.0 (`brew install cbmc`).

## What ran

`reproduce.sh` compiles two ST programs with the **real `iec2c`** and checks the
**real MATIEC-generated C** (`config.c`/`res.c`/`POUS.c`) with **real CBMC**:

| Program (compiled by real `iec2c`) | Property A `!Light \|\| Btn` | CBMC verdict |
| --- | --- | --- |
| `timer_faithful.st` — scan-counting TON (K-LD's semantics) | holds | **VERIFICATION SUCCESSFUL** (proved) |
| `timer_havoc.st` — timer output left unconstrained | can break | **VERIFICATION FAILED** (counterexample) |

The loop is fully unwound (6 scans, `--unwind 8`), so `SUCCESSFUL` on the faithful
program is a **complete proof over all length-6 input traces**, not sampling.

## Why this matters

This is the WP1a claim, demonstrated on genuine MATIEC codegen rather than a hand
model: a faithful independent engine (MATIEC-C + CBMC) **proves property A safe**,
siding with K-LD, while the havoc timer — the ESBMC "simple format" defect —
**manufactures the exact false alarm** ESBMC reports. Two independent engines
(K-LD and MATIEC-C+CBMC) now agree against ESBMC on the mechanism behind
Discrepancy 1.

## Honest caveat — the standard library

A locally-built `iec2c` (bison 3.x) does not load matiec's standard-FB library, so
the library `TON` (wall-clock, `__CURRENT_TIME`-driven) is unavailable here. The
timer is therefore written as the equivalent **scan-counting** state machine in ST
— the exact faithful semantics K-LD implements and the paper reasons about
(`ET=0` on the trigger edge, fires after `PT` scans). This changes *how the timer
is expressed in ST*, not *what is verified*: real `iec2c` still performs the
LD/ST→C lowering and real CBMC still discharges the property.

The **library-`TON` path** (wall-clock FB body from `iec_std_FB.h`) is what
`../run_wp1a.sh` exercises via the OpenPLC container, whose `iec2c` loads the
standard library correctly. That is the path to use for the paper's real
PLCopen-XML benchmarks.

## Reproduce

```bash
# build matiec once (needs modern bison: brew install bison)
git clone --depth 1 https://github.com/thiagoralves/matiec.git
cd matiec && PATH="$(brew --prefix bison)/bin:$PATH" sh -c 'autoreconf -i && ./configure && make -j4'
# then, from this directory:
MATIEC=/path/to/matiec bash reproduce.sh
```

Expected output:
```
  faithful  : ... prop A: !Light || Btn: SUCCESS VERIFICATION SUCCESSFUL   [expected: prop A SUCCESS]
  havoc     : ... prop A: !Light || Btn: FAILURE VERIFICATION FAILED
```
