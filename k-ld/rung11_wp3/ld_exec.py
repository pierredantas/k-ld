#!/usr/bin/env python3
"""
ld_exec.py -- a faithful executor of the K-LD DSL fragment, used as the WP3
fault-injection *measurement* instrument.

K-LD's krun is the canonical oracle; it is not installed in the authoring
environment. This module re-implements the same scan-cycle semantics (contacts,
OTE/OTL/OTU with retention, TON/TOF/TP, CTU/CTD, edges via prev-value) so the
mutation campaign can compute behavioral- and property-detection for every mutant
here. It is validated two ways (see validate_exec.py):
  1. it reproduces the paper's RQ1 reference done-bit traces (Table 2) exactly;
  2. it agrees with NuSMV on the WP2 members that have SMV encodings.
So the campaign numbers are trustworthy; the canonical run is still differential.py.

Timer/counter semantics match the paper's faithful (MATIEC-validated) state
machines: elapsed measured from the trigger edge, Delta t = 1 scan, counters
saturate, resets/loads dominant.
"""
import re

# ---- parsing ----------------------------------------------------------------
def _split_top(s):
    """Split on top-level commas (respecting parentheses)."""
    parts, depth, cur = [], 0, ""
    for c in s:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        if c == "," and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += c
    if cur.strip():
        parts.append(cur)
    return [p.strip() for p in parts]

def parse(text):
    rungs = []
    # strip // comments, join, split on ';'
    body = "\n".join(l.split("//", 1)[0] for l in text.splitlines())
    for stmt in body.split(";"):
        s = stmt.strip()
        if not s:
            continue
        m = re.match(r"^(OTE|OTL|OTU)\((\w+)\)\s*:=\s*(.+)$", s, re.S)
        if m:
            rungs.append((m.group(1), m.group(2), m.group(3).strip())); continue
        m = re.match(r"^(TON|TOF|TP)\((\w+)\s*,\s*(\d+)\s*,\s*(.+)\)$", s, re.S)
        if m:
            rungs.append((m.group(1), m.group(2), int(m.group(3)), m.group(4).strip())); continue
        m = re.match(r"^(CTU|CTD)\((\w+)\s*,\s*(\d+)\s*,\s*(.+)\)$", s, re.S)
        if m:
            a, b = _split_top(m.group(4))
            rungs.append((m.group(1), m.group(2), int(m.group(3)), a.strip(), b.strip())); continue
        raise ValueError(f"cannot parse rung: {s!r}")
    return rungs

# ---- Boolean-expression evaluation (XIC/XIO, * = AND, + = OR) ----------------
def eval_bexp(expr, image):
    # recursive descent: OR over AND over atoms
    pos = 0
    toks = re.findall(r"XIC|XIO|\(|\)|\*|\+|\w+", expr)
    i = 0
    def peek(): return toks[i] if i < len(toks) else None
    def atom():
        nonlocal i
        t = toks[i]
        if t in ("XIC", "XIO"):
            i += 1; assert toks[i] == "("; i += 1
            v = toks[i]; i += 1; assert toks[i] == ")"; i += 1
            return image.get(v, False) if t == "XIC" else not image.get(v, False)
        if t == "(":
            i += 1; v = _or(); assert toks[i] == ")"; i += 1; return v
        raise ValueError(f"bad atom {t}")
    def _and():
        v = atom()
        while peek() == "*":
            nonlocal i; i += 1; v = atom() and v
        return v
    def _or():
        v = _and()
        while peek() == "+":
            nonlocal i; i += 1; v = _and() or v
        return v
    return _or()

# ---- scan-cycle executor ----------------------------------------------------
class Exec:
    def __init__(self, rungs):
        self.rungs = rungs
        self.image = {}
        self.tmr = {}   # inst -> dict(et, running, prev)
        self.cnt = {}   # inst -> dict(cv, prev)

    def _ton(self, inst, PT, IN):
        # Elapsed measured from the trigger edge: ET=0 on the edge scan, then
        # increments each held scan (MATIEC/paper RQ1 semantics; fires after PT).
        st = self.tmr.setdefault(inst, {"et": 0, "prev": False})
        if IN and not st["prev"]:
            st["et"] = 0
        elif IN and st["et"] < PT:
            st["et"] += 1
        if not IN:
            st["et"] = 0
        st["prev"] = IN
        return IN and st["et"] >= PT

    def _tof(self, inst, PT, IN):
        st = self.tmr.setdefault(inst, {"et": PT})
        if IN:
            st["et"] = 0; q = True
        else:
            if st["et"] < PT: st["et"] += 1; q = True
            else: q = False
        return q

    def _tp(self, inst, PT, IN):
        st = self.tmr.setdefault(inst, {"et": 0, "running": False, "prev": False})
        rising = IN and not st["prev"]
        if rising and not st["running"]:
            st["running"] = True; st["et"] = 0
        if st["running"]:
            q = True; st["et"] += 1
            if st["et"] >= PT: st["running"] = False
        else:
            q = False
        st["prev"] = IN
        return q

    def _ctu(self, inst, PV, CU, R):
        st = self.cnt.setdefault(inst, {"cv": 0, "prev": False})
        if R:
            st["cv"] = 0
        elif CU and not st["prev"] and st["cv"] < PV:
            st["cv"] += 1
        st["prev"] = CU
        return st["cv"] >= PV

    def _ctd(self, inst, PV, CD, LD):
        st = self.cnt.setdefault(inst, {"cv": PV, "prev": False})
        if LD:
            st["cv"] = PV
        elif CD and not st["prev"] and st["cv"] > 0:
            st["cv"] -= 1
        st["prev"] = CD
        return st["cv"] <= 0

    def scan(self, inputs):
        self.image.update(inputs)
        for r in self.rungs:
            k = r[0]
            if k == "OTE":
                self.image[r[1]] = eval_bexp(r[2], self.image)
            elif k == "OTL":
                if eval_bexp(r[2], self.image): self.image[r[1]] = True
            elif k == "OTU":
                if eval_bexp(r[2], self.image): self.image[r[1]] = False
            elif k in ("TON", "TOF", "TP"):
                IN = eval_bexp(r[3], self.image)
                fn = {"TON": self._ton, "TOF": self._tof, "TP": self._tp}[k]
                self.image[r[1]] = fn(r[1], r[2], IN)
            elif k in ("CTU", "CTD"):
                a = eval_bexp(r[3], self.image); b = eval_bexp(r[4], self.image)
                fn = {"CTU": self._ctu, "CTD": self._ctd}[k]
                self.image[r[1]] = fn(r[1], r[2], a, b)
        return dict(self.image)

def run(ld_text, input_trace):
    """input_trace: list of {inputvar: bool}. Returns list of per-scan images."""
    ex = Exec(parse(ld_text))
    return [ex.scan(step) for step in input_trace]
