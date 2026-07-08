#!/usr/bin/env python3
"""Shared helpers for the WP3 campaign: input-trace generation and property
evaluation, matching rung6/differential.py's semantics (invariant / absence /
mutual_exclusion; bounded enumerated inputs over several sweeps)."""
import re, itertools, json

# ---- input trace: enumerate all 2^k assignments, repeated over sweeps -------
def make_trace(input_vars, sweeps=3, cap=48):
    k = len(input_vars)
    combos = list(itertools.product([False, True], repeat=k)) if k else [()]
    if len(combos) > cap:
        allF = tuple([False]*k); allT = tuple([True]*k)
        combos = [allF, allT] + combos[1:cap-1]
    trace = []
    for _ in range(sweeps):
        for c in combos:
            trace.append({v: b for v, b in zip(input_vars, c)})
    return trace

# ---- property parsing (props.yaml) ------------------------------------------
def load_props(path):
    props, cur = [], None
    for line in open(path):
        s = line.strip()
        m = re.match(r"-\s*id:\s*(\S+)", s)
        if m:
            cur = {"id": m.group(1), "kind": "invariant"}; props.append(cur); continue
        if cur is None: continue
        mk = re.match(r"kind:\s*(\S+)", s)
        if mk: cur["kind"] = mk.group(1)
        me = re.match(r'expression:\s*"(.*)"', s)
        if me: cur["expr"] = me.group(1)
        mv = re.match(r"variables:\s*\[(.*?)\]", s)
        if mv: cur["vars"] = [x.strip() for x in mv.group(1).split(",") if x.strip()]
    return props

# ---- property evaluation on one image ---------------------------------------
def _eval_expr(expr, image):
    names = set(re.findall(r"[A-Za-z_]\w*", expr))
    env = {n: bool(image.get(n, False)) for n in names}
    py = re.sub(r"!", " not ", expr).replace("&&", " and ").replace("||", " or ")
    return bool(eval(py, {"__builtins__": {}}, env))

def prop_holds(p, image):
    if p["kind"] == "mutual_exclusion":
        return sum(1 for v in p["vars"] if image.get(v, False)) <= 1
    v = _eval_expr(p["expr"], image)
    return (not v) if p["kind"] == "absence" else v   # absence: expr is BAD

def evaluate(images, props):
    """Return (verdict, frozenset_of_violated_ids). verdict: 'safe'|'unsafe'."""
    violated = set()
    for p in props:
        for img in images:
            if not prop_holds(p, img):
                violated.add(p["id"]); break
    return ("unsafe" if violated else "safe"), frozenset(violated)

def load_kinds(path):
    return json.load(open(path))["kinds"]
