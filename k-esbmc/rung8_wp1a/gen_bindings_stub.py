#!/usr/bin/env python3
"""
WP1a bindings-stub generator  --  auto-write bindings.h for the MATIEC+CBMC run.

bindings.h is the single per-benchmark integration point (see README): it maps
the harness macros VAR(x)/IN(x)/OUT(x) onto the C symbols MATIEC emits, and
model_init()/model_scan() onto MATIEC's resource entry points. This script
produces a first-cut bindings.h automatically so the first real run needs no
hand mapping; a human should still eyeball the result before trusting a verdict.

The mapping chain is:

    friendly name  --(PLCopen XML)-->  located address (%IX0.0)
    located address  --(LOCATED_VARIABLES.h)-->  MATIEC symbol (__IX0_0)

Inputs/outputs in the benchmark suite are located variables (%IX/%QX), so they
resolve cleanly. A property variable that is a *non-located local* (e.g. a phase
flag living inside a POU instance struct) cannot be reached by address; those are
emitted as clearly-marked TODOs for manual completion.

This is a SKETCH: MATIEC/OpenPLC layouts vary across builds. Validate the emitted
symbols against your container's generated C, and flip WP1A_LOCATED_POINTERS (see
the emitted header) if your build declares located vars as pointers rather than
plain globals.

Usage:
  gen_bindings_stub.py <prog>.json <LOCATED_VARIABLES.h> <prog>.xml [props.yaml] > bindings.h
"""
import json, re, sys, xml.etree.ElementTree as ET

def strip_ns(tag):                      # "{http://…}variable" -> "variable"
    return tag.rsplit("}", 1)[-1]

# --- LOCATED_VARIABLES.h : address -> (symbol, ctype, direction) --------------
# Line form: __LOCATED_VAR(IEC_BOOL,__IX0_0,I,X,0,0)
_LOC = re.compile(
    r"__LOCATED_VAR\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([IQM])\s*,"
    r"\s*([XBWDL])\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")
def parse_located(path):
    addr2sym = {}
    for line in open(path):
        m = _LOC.search(line)
        if not m:
            continue
        ctype, sym, direction, size, major, minor = m.groups()
        addr = f"%{direction}{size}{major}.{minor}"          # %IX0.0
        addr2sym[addr] = (sym, ctype, direction)
    return addr2sym

# --- PLCopen XML : friendly name -> located address ---------------------------
def parse_xml_addresses(path):
    name2addr = {}
    root = ET.parse(path).getroot()
    for el in root.iter():
        if strip_ns(el.tag) != "variable":
            continue
        name = el.get("name")
        if not name:
            continue
        # address may be an attribute or a child <address value="%IX0.0"/> / text
        addr = el.get("address")
        if addr is None:
            for ch in el:
                if strip_ns(ch.tag) == "address":
                    addr = ch.get("value") or (ch.text or "").strip()
                    break
        if addr:
            name2addr[name] = addr.strip()
    return name2addr

# --- property variables actually referenced (to warn precisely) ---------------
_KEYWORDS = {"true", "false", "TRUE", "FALSE"}
def prop_vars(path):
    if not path:
        return set()
    vs = set()
    for line in open(path):
        s = line.strip()
        if s.startswith("expression:"):
            expr = s.split(":", 1)[1].strip().strip('"').strip("'")
            vs |= {t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr)
                   if t not in _KEYWORDS}
        elif s.startswith("- ") and not s.startswith("- id:"):
            vs.add(s[2:].strip().strip('"').strip("'"))     # mutual_exclusion list item
    return vs

def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    kinds = json.load(open(sys.argv[1]))["kinds"]
    addr2sym = parse_located(sys.argv[2])
    name2addr = parse_xml_addresses(sys.argv[3])
    needed = prop_vars(sys.argv[4]) if len(sys.argv) > 4 else set()

    resolved, todo = {}, []
    for name, kind in kinds.items():
        if kind == "local":
            continue                                        # locals aren't harness inputs
        addr = name2addr.get(name)
        sym = addr2sym.get(addr, (None,))[0] if addr else None
        if sym:
            resolved[name] = sym
        else:
            todo.append((name, kind, addr))
    # property vars that are locals / unresolved but DO matter
    for v in sorted(needed):
        if v not in resolved and v not in kinds:
            todo.append((v, "prop-ref (unknown)", None))
        elif v not in resolved and kinds.get(v) == "local":
            todo.append((v, "local referenced by a property", name2addr.get(v)))

    w = sys.stdout.write
    w("/* AUTO-STUBBED by gen_bindings_stub.py -- REVIEW before trusting a verdict. */\n")
    w("#ifndef BINDINGS_H\n#define BINDINGS_H\n")
    w('#include "iec_std_lib.h"   /* IEC_BOOL and the located-var externs */\n\n')
    w("/* If your OpenPLC build declares located vars as POINTERS (IEC_BOOL *__IX0_0),\n"
      "   define WP1A_LOCATED_POINTERS so VAR(x) dereferences them. Default: plain globals. */\n")
    w("#ifdef WP1A_LOCATED_POINTERS\n  #define LOC(sym) (*sym)\n#else\n  #define LOC(sym) sym\n#endif\n\n")

    for name, sym in resolved.items():
        w(f"#define __SYM_{name} {sym}\n")
    w("\n#define IN(x)  LOC(__SYM_##x)\n#define OUT(x) LOC(__SYM_##x)\n#define VAR(x) LOC(__SYM_##x)\n\n")

    # MATIEC resource entry points -> harness's model_init/model_scan
    w("/* Resource entry points generated by MATIEC (names may be config/res specific). */\n")
    w("extern void config_init__(void);\n")
    w("extern void config_run__(unsigned long tick);\n")
    w("static unsigned long __wp1a_tick = 0;\n")
    w("static inline void model_init(void){ config_init__(); __wp1a_tick = 0; }\n")
    w("static inline void model_scan(void){ config_run__(__wp1a_tick++); }\n")

    if todo:
        w("\n/* ---- UNRESOLVED: complete these by hand ------------------------------\n")
        for name, kind, addr in todo:
            w(f"   {name:24s} kind={kind:28s} addr={addr}\n")
        w("   (locals live inside a POU instance struct, e.g. RES0__INSTANCE0.PHASE_NS_GREEN;\n")
        w("    add  #define __SYM_<name> <that lvalue>  above.)\n")
        w("   -------------------------------------------------------------------- */\n")
        sys.stderr.write(f"[gen_bindings_stub] {len(resolved)} resolved, "
                         f"{len(todo)} UNRESOLVED (see TODO block in bindings.h)\n")
    w("#endif\n")

if __name__ == "__main__":
    main()
