#!/usr/bin/env python3
"""
plcopen2kld -- independent frontend for K-LD's Rung 6 differential (E3).

Translates the *simplified* PLCopen rung format (linear <contact> series + <coil>,
plus TON/TOF/TP <block>s) used by the ESBMC-PLC benchmarks into K-LD DSL.
Emits both the .ld program and a JSON sidecar classifying inputs/outputs/locals so
the differential harness knows what to drive and what to observe.

Scope (phase 1): contacts (negated -> XIO / plain -> XIC) in series (AND), coils
with storage set/reset -> OTL/OTU else OTE, and TON/TOF/TP timer blocks.
Parallel branches and the graphical netlist format are out of scope here.
"""
import sys, re, json, os, xml.etree.ElementTree as ET


def strip_ns(root):
    for e in root.iter():
        e.tag = re.sub(r'^\{.*\}', '', e.tag)
    return root


def parse(path):
    root = strip_ns(ET.parse(path).getroot())
    pou = root.find('.//pou')
    iface = pou.find('interface')

    kinds = {}   # var -> 'input'|'output'|'local'  (BOOL vars only)
    types = {}   # var -> type tag (BOOL, INT, ...)
    for sect, kind in (('inputVars', 'input'), ('outputVars', 'output'),
                       ('localVars', 'local'), ('externalVars', 'input')):
        for vs in iface.findall(sect):
            for v in vs.findall('variable'):
                ty = v.find('type')
                tag = ty[0].tag if (ty is not None and len(ty)) else 'BOOL'
                types[v.get('name')] = tag
                if tag == 'BOOL':                       # only BOOL bits enter the image
                    kinds[v.get('name')] = kind

    # initial values (e.g. a timer preset PT declared with an initialValue)
    initials = {}
    for v in iface.iter('variable'):
        iv = v.find('.//initialValue')
        if iv is not None:
            txt = ''.join(iv.itertext()).strip()
            initials[v.get('name')] = txt

    rungs = []
    for rung in pou.findall('.//LD/rung'):
        contacts, coils, blocks = [], [], []
        for el in rung:
            if el.tag == 'contact':
                neg = el.get('negated') is not None
                contacts.append((el.get('variable'), neg))
            elif el.tag == 'coil':
                storage = el.get('storage')      # set | reset | None
                coils.append((el.get('variable'), storage))
            elif el.tag == 'block':
                params = {v.get('formalParameter'): ''.join(v.itertext()).strip()
                          for v in el.findall('variable')}
                blocks.append((el.get('typeName'), el.get('instanceName'), params))
        rungs.append((contacts, coils, blocks))
    return kinds, rungs, initials


def rung_expr(contacts):
    """Series contacts -> K-LD BExp (AND of XIC/XIO). Empty -> the power rail (TRUE)."""
    if not contacts:
        return None
    terms = [f"{'XIO' if neg else 'XIC'}({v})" for (v, neg) in contacts]
    return " * ".join(terms)


def parse_time(txt, default):
    """Parse a preset value: a T# literal (seconds) or a plain int; else default."""
    if txt is None:
        return default
    m = re.search(r'T#(\d+)s', txt)
    if m:
        return int(m.group(1))
    if re.fullmatch(r'\d+', txt.strip()):
        return int(txt.strip())
    return default


def translate(kinds, rungs, initials, default_pt):
    out, timers = [], []
    for (contacts, coils, blocks) in rungs:
        expr = rung_expr(contacts)
        for (var, storage) in coils:
            e = expr if expr is not None else "XIC(__RAIL)"  # rail-fed coil
            if storage == 'set':
                out.append(f"OTL({var}) := {e} ;")
            elif storage == 'reset':
                out.append(f"OTU({var}) := {e} ;")
            else:
                out.append(f"OTE({var}) := {e} ;")
        for (typ, inst, params) in blocks:
            if typ in ('TON', 'TOF', 'TP'):
                q_var = params.get('Q')                       # done bit -> K-LD instance Id
                in_var = params.get('IN')
                pt = parse_time(initials.get(params.get('PT', '')), default_pt)
                in_expr = f"XIC({in_var})" if in_var else "XIC(__RAIL)"
                out.append(f"{typ}({q_var}, {pt}, {in_expr}) ;")
                timers.append({'id': q_var, 'kind': typ, 'pt': pt, 'in': in_var})
            else:
                out.append(f"// UNSUPPORTED block {typ} {inst}")
    return out, timers


def main():
    path = sys.argv[1]
    default_pt = int(os.environ.get('KLD_DEFAULT_PT', '2'))
    kinds, rungs, initials = parse(path)
    program, timers = translate(kinds, rungs, initials, default_pt)
    print("\n".join(program))
    if len(sys.argv) > 2:                       # emit JSON sidecar
        timer_ids = {t['id'] for t in timers}
        with open(sys.argv[2], 'w') as f:
            json.dump({'kinds': kinds,
                       'inputs':  [v for v, k in kinds.items() if k == 'input'],
                       'outputs': [v for v, k in kinds.items() if k == 'output'],
                       # timer done-bits are driven by K-LD, not free state bits
                       'locals':  [v for v, k in kinds.items()
                                   if k == 'local' and v not in timer_ids],
                       'timers':  timers},
                      f, indent=2)


if __name__ == '__main__':
    main()
