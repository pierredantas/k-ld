# K-LD build & run targets.
#
# Two ways to run:
#   (A) Host K on PATH (Nix/kup install) -- use the plain targets: build, test-*.
#   (B) K inside Docker (no host install) -- use the d-* wrappers, which run the
#       plain targets inside the container. This is the supported path on macOS
#       (no K macOS binary; amd64 image under emulation).
#
# Ground truth for conformance: OpenPLC v3 (Docker).

K       ?= kompile
KRUN    ?= krun
MAIN    ?= ld.k
KOMPILED = ld-kompiled

# ---- Docker wrappers (path B) ---------------------------------------------
IMAGE     ?= k-ld:latest
PLATFORM  ?= linux/amd64
DOCKER_RUN = docker run --rm --platform $(PLATFORM) -v "$(CURDIR)":/work $(IMAGE)

.PHONY: image d-build d-test-and d-test-and-neg d-test-latch d-test-ton d-test-tof d-test-tp d-test-ctu d-test-ctd d-prove-build d-prove d-shell

d-prove-build: image
	$(DOCKER_RUN) make prove-build

d-prove: image
	$(DOCKER_RUN) make prove

d-prove-timer: image
	$(DOCKER_RUN) make prove-timer

image:
	docker build --platform $(PLATFORM) -t $(IMAGE) .

d-build: image
	$(DOCKER_RUN) make build

d-test-and: image
	$(DOCKER_RUN) make test-and

d-test-and-neg: image
	$(DOCKER_RUN) make test-and-neg

d-test-latch: image
	$(DOCKER_RUN) make test-latch

d-test-ton: image
	$(DOCKER_RUN) make test-ton

d-test-tof: image
	$(DOCKER_RUN) make test-tof

d-test-tp: image
	$(DOCKER_RUN) make test-tp

d-test-ctu: image
	$(DOCKER_RUN) make test-ctu

d-test-ctd: image
	$(DOCKER_RUN) make test-ctd

d-shell: image
	docker run --rm -it --platform $(PLATFORM) -v "$(CURDIR)":/work $(IMAGE) bash
# ---------------------------------------------------------------------------

.PHONY: build test-and clean

# Rung 0 check: is K installed?
check:
	@command -v $(K) >/dev/null 2>&1 && echo "K found: $$( $(K) --version | head -1 )" \
	  || echo "K NOT found -- run the Rung 0 install first."

build: $(KOMPILED)
$(KOMPILED): $(MAIN) ld-syntax.k
	$(K) $(MAIN)

# --- Rung 2 regressions (now driven through the 1-scan harness) --------------
# E1: I0=I1=true (via input overlay) => expect Q0 |-> true in image + trace.
test-and: build
	$(KRUN) tests/and_rung.ld \
	  -cIMAGE='I0 |-> false I1 |-> false Q0 |-> false' \
	  -cTIMERS=.Map -cDT=1 -cCOUNTERS=.Map \
	  -cINPUTS='ListItem(I0 |-> true I1 |-> true)' \
	  --output pretty

# E1 negative: I0=true, I1=false => expect Q0 |-> false.
test-and-neg: build
	$(KRUN) tests/and_rung.ld \
	  -cIMAGE='I0 |-> false I1 |-> false Q0 |-> false' \
	  -cTIMERS=.Map -cDT=1 -cCOUNTERS=.Map \
	  -cINPUTS='ListItem(I0 |-> true I1 |-> false)' \
	  --output pretty

# --- Rung 3: retention across scans ------------------------------------------
# E2 latch: scan1 I0 pulses -> Q0 latched; scan2 I0 drops -> Q0 RETAINS true;
# scan3 I1 pulses -> Q0 unlatched; scan4 -> retains false.
# Expected <trace> Q0 sequence: true, true, false, false.
test-latch: build
	$(KRUN) tests/latch.ld \
	  -cIMAGE='I0 |-> false I1 |-> false Q0 |-> false' \
	  -cTIMERS=.Map -cDT=1 -cCOUNTERS=.Map \
	  -cINPUTS='ListItem(I0 |-> true I1 |-> false) ListItem(I0 |-> false I1 |-> false) ListItem(I0 |-> false I1 |-> true) ListItem(I0 |-> false I1 |-> false)' \
	  --output pretty

# --- Rung 4: on-delay timer (OpenPLC/MATIEC-validated) -----------------------
# TON T0, PT=3, DT=1. I0 true for scans 1-4 then false at scan 5. Elapsed is 0 on
# the trigger scan, so it fires PT/DT=3 scans after the edge (scan 4).
# Expected T0 (done) trace: F,F,F,T,F.
test-ton: build
	$(KRUN) tests/ton.ld \
	  -cIMAGE='I0 |-> false T0 |-> false' \
	  -cTIMERS='T0 |-> tstate(0, 0, false)' -cCOUNTERS=.Map \
	  -cDT=1 \
	  -cINPUTS='ListItem(I0 |-> true) ListItem(I0 |-> true) ListItem(I0 |-> true) ListItem(I0 |-> true) ListItem(I0 |-> false)' \
	  --output pretty

# TOF T0, PT=3, DT=1. IN=I0 high scans 1-2 then low. Q holds true for PT after the
# falling edge (elapsed 0 at the edge). Expected T0 trace: T,T,T,T,T,F.
test-tof: build
	$(KRUN) tests/tof.ld \
	  -cIMAGE='I0 |-> false T0 |-> false' \
	  -cTIMERS='T0 |-> tstate(0, 0, false)' -cCOUNTERS=.Map \
	  -cDT=1 \
	  -cINPUTS='ListItem(I0 |-> true) ListItem(I0 |-> true) ListItem(I0 |-> false) ListItem(I0 |-> false) ListItem(I0 |-> false) ListItem(I0 |-> false)' \
	  --output pretty

# TP T0, PT=3, DT=1. IN=I0: F,T,T,T,F,T. Fixed PT-long pulse from the rising edge
# (elapsed 0 at edge), IN ignored during the pulse; re-arms when IN goes low.
# Expected T0 trace: F,T,T,T,F,T.
test-tp: build
	$(KRUN) tests/tp.ld \
	  -cIMAGE='I0 |-> false T0 |-> false' \
	  -cTIMERS='T0 |-> tstate(0, 0, false)' -cCOUNTERS=.Map \
	  -cDT=1 \
	  -cINPUTS='ListItem(I0 |-> false) ListItem(I0 |-> true) ListItem(I0 |-> true) ListItem(I0 |-> true) ListItem(I0 |-> false) ListItem(I0 |-> true)' \
	  --output pretty

# --- Rung 5: counters --------------------------------------------------------
# CTU C0, PV=2. I0=CU (edge), I1=R (reset). Sequence exercises: edge counting
# (held-high does not double count), reaching preset, reset dominance.
# I0: F,T,T,F,T,T,F   I1: F,F,F,F,F,T,F   Expected C0 (Q) trace: F,F,F,F,T,F,F.
test-ctu: build
	$(KRUN) tests/ctu.ld \
	  -cIMAGE='I0 |-> false I1 |-> false C0 |-> false' \
	  -cCOUNTERS='C0 |-> cstate(0, false)' -cTIMERS=.Map -cDT=1 \
	  -cINPUTS='ListItem(I0 |-> false I1 |-> false) ListItem(I0 |-> true I1 |-> false) ListItem(I0 |-> true I1 |-> false) ListItem(I0 |-> false I1 |-> false) ListItem(I0 |-> true I1 |-> false) ListItem(I0 |-> true I1 |-> true) ListItem(I0 |-> false I1 |-> false)' \
	  --output pretty

# CTD C0, PV=2. I0=CD (edge), I1=LD (load). Load, count down to 0 (floor),
# reload. I0: F,T,T,F,T,T,F   I1: T,F,F,F,F,F,T   Expected C0 trace: F,F,F,F,T,T,F.
test-ctd: build
	$(KRUN) tests/ctd.ld \
	  -cIMAGE='I0 |-> false I1 |-> false C0 |-> false' \
	  -cCOUNTERS='C0 |-> cstate(0, false)' -cTIMERS=.Map -cDT=1 \
	  -cINPUTS='ListItem(I0 |-> false I1 |-> true) ListItem(I0 |-> true I1 |-> false) ListItem(I0 |-> true I1 |-> false) ListItem(I0 |-> false I1 |-> false) ListItem(I0 |-> true I1 |-> false) ListItem(I0 |-> true I1 |-> false) ListItem(I0 |-> false I1 |-> true)' \
	  --output pretty

# --- Rung 8: machine-checked construct lemmas (kprove, Haskell backend) ------
HS_KOMPILED = ld-haskell

prove-build: $(HS_KOMPILED)
$(HS_KOMPILED): $(MAIN) ld-syntax.k ld-proof.k
	$(K) --backend haskell ld-proof.k --main-module LD-PROOF --syntax-module LD-SYNTAX -o $(HS_KOMPILED)

prove: prove-build
	kprove proof/verification.k --definition $(HS_KOMPILED)

prove-timer: prove-build
	kprove proof/timer-spec.k --definition $(HS_KOMPILED)

clean:
	rm -rf $(KOMPILED) $(HS_KOMPILED) .kompile-* .krun-* .kprove-*
