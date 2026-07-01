#!/usr/bin/env python3
"""
graphical2kld -- automated frontend for the GRAPHICAL PLCopen LD format
(power rails + contacts/coils/blocks wired by localId/refLocalId), producing K-LD
DSL + a JSON sidecar. Complements plcopen2kld.py (which handles the simple <rung>
format).

Netlist resolution:
  * leftPowerRail            -> TRUE
  * contact (series)         -> resolve(input) AND term
  * multiple connections in  -> OR (parallel branches)
  * coil storage set/reset   -> OTL/OTU, else OTE
  * TON/TOF/TP block         -> timer instruction; its Q output (instance "<name>_Q")
                                is read downstream as XIC(<name>_Q)
  * edge="rising"/"falling"  -> modelled with prev-value helper coils (R_TRIG/F_TRIG):
                                rise_X := X AND NOT prev_X ; prev_X := X (updated last)

Known limitation: a set/reset coil pair on the same variable is emitted directly, so
a rising edge that both sets and resets in one scan can race; snapshotting is TODO.

Usage: graphical2kld.py <bench.ld> [sidecar.json]
"""
import sys, re, json, os, xml.etree.ElementTree as ET


def strip_ns(root):
    for e in root.iter():
        e.tag = re.sub(r'^\{.*\}', '', e.tag)
    return root


def load_xml(path):
    """Parse, tolerating undeclared namespace prefixes (some benchmarks use
    <xhtml:p> in docs without declaring xmlns:xhtml). Inject any missing decls
    on the root element before parsing."""
    txt = open(path, encoding='utf-8').read()
    used = set(re.findall(r'<(\w+):', txt))
    declared = set(re.findall(r'xmlns:(\w+)=', txt))
    missing = used - declared
    if missing:
        inject = ' '.join(f'xmlns:{p}="urn:{p}"' for p in sorted(missing))
        txt = re.sub(r'(<project\b)', r'\1 ' + inject, txt, count=1)
    return ET.fromstring(txt)


def parse_time(txt, default):
    if txt:
        m = re.search(r'T#(\d+)s', txt)
        if m:
            return int(m.group(1))
        if re.fullmatch(r'\d+', txt.strip()):
            return int(txt.strip())
    return default


class G:
    def __init__(self, path, default_pt):
        self.default_pt = default_pt
        root = strip_ns(load_xml(path))
        pou = root.find('.//pou')
        iface = pou.find('interface')

        self.kinds, self.types = {}, {}
        for sect, kind in (('inputVars', 'input'), ('outputVars', 'output'),
                           ('localVars', 'local'), ('externalVars', 'input')):
            for vs in iface.findall(sect):
                for v in vs.findall('variable'):
                    ty = v.find('type')
                    tag = ty[0].tag if (ty is not None and len(ty)) else 'BOOL'
                    self.types[v.get('name')] = tag
                    if tag != 'BOOL':
                        continue
                    # In the graphical format, I/O direction is given by the
                    # located address (%IX = input, %QX = output), overriding the
                    # declaring section (often everything is under localVars).
                    addr = v.get('address') or ''
                    if addr.startswith('%I'):
                        k = 'input'
                    elif addr.startswith('%Q'):
                        k = 'output'
                    else:
                        k = kind
                    self.kinds[v.get('name')] = k

        # index every LD element by localId
        self.els = {}
        ld = pou.find('.//LD')
        for e in ld:
            lid = e.get('localId')
            if lid is None:
                continue
            self.els[lid] = e

        self.edges = {}      # var -> set of edge kinds ('rising'/'falling')
        self.timers = []     # {'id','kind','pt'}
        self.counters = []   # {'id','kind','pv'}
        self.extra_locals = set()
        self.memo = {}

    # ---- connection helpers --------------------------------------------------
    def in_conns(self, e, formal=None):
        """List of (refLocalId, refFormalParameter) feeding a connectionPointIn.
        For blocks, `formal` selects the input variable (IN/PT)."""
        node = e
        if e.tag == 'block' and formal is not None:
            for v in e.findall('.//inputVariables/variable'):
                if v.get('formalParameter') == formal:
                    node = v
                    break
            else:
                return []
        conns = []
        for cin in node.findall('.//connectionPointIn'):
            for c in cin.findall('connection'):
                conns.append((c.get('refLocalId'), c.get('formalParameter')))
        return conns

    # ---- boolean-expression combinators (with TRUE simplification) ----------
    @staticmethod
    def AND(a, b):
        if a == 'TRUE':
            return b
        if b == 'TRUE':
            return a
        wa = f"( {a} )" if '+' in a else a        # parenthesise OR-operands: * binds tighter
        wb = f"( {b} )" if '+' in b else b
        return f"{wa} * {wb}"

    @staticmethod
    def OR(parts):
        parts = [p for p in parts if p]
        if not parts:
            return 'TRUE'
        if 'TRUE' in parts:
            return 'TRUE'
        return " + ".join(f"( {p} )" if '+' in p else p for p in parts)

    def term(self, e):
        var = e.findtext('variable')
        neg = e.get('negated') in ('true', 'negated', '1')   # explicit value in graphical fmt
        edge = e.get('edge')
        if edge in ('rising', 'falling'):
            self.edges.setdefault(var, set()).add(edge)
            base = ('rise_' if edge == 'rising' else 'fall_') + var
            self.extra_locals.add(base)
            return f"XIO({base})" if neg else f"XIC({base})"
        return f"XIO({var})" if neg else f"XIC({var})"

    # ---- resolve the driver expression reaching an input point --------------
    def resolve(self, lid, out_fp=None):
        key = (lid, out_fp)
        if key in self.memo:
            return self.memo[key]
        e = self.els.get(lid)
        if e is None:
            return 'TRUE'
        tag = e.tag
        if tag == 'leftPowerRail':
            res = 'TRUE'
        elif tag == 'contact':
            branches = [self.resolve(r, f) for (r, f) in self.in_conns(e)]
            inexpr = self.OR(branches) if branches else 'TRUE'
            res = self.AND(inexpr, self.term(e))
        elif tag == 'block':                       # a timer output reference
            qv = f"{e.get('instanceName')}_{out_fp or 'Q'}"
            res = f"XIC({qv})"
        elif tag == 'inVariable':
            expr = (e.findtext('expression') or '').strip()
            if expr in ('TRUE', 'FALSE'):
                res = 'TRUE' if expr == 'TRUE' else 'XIO(__never)'
            else:
                res = f"XIC({expr})"
        elif tag == 'coil':
            res = f"XIC({e.findtext('variable')})"
        else:
            res = 'TRUE'
        self.memo[key] = res
        return res

    def in_expr(self, e, formal):
        return self.OR([self.resolve(r, f) for (r, f) in self.in_conns(e, formal)])

    def in_int(self, e, formal, default):
        """A numeric input (timer PT / counter PV) wired to an inVariable literal."""
        conns = self.in_conns(e, formal)
        if conns:
            tgt = self.els.get(conns[0][0])
            if tgt is not None:
                return parse_time(tgt.findtext('expression'), default)
        return default

    # ---- build the K-LD program ---------------------------------------------
    def build(self):
        logic = []      # (sort-key, line)
        fb_post = []    # postlude lines for edge-FB prev updates
        for lid, e in self.els.items():
            if e.tag != 'block':
                if e.tag == 'coil':
                    var = e.findtext('variable')
                    drv = self.OR([self.resolve(r, f) for (r, f) in self.in_conns(e)])
                    if drv == 'TRUE':
                        drv = f"XIC({var}) + XIO({var})"   # tautology = always energised
                    st = e.get('storage')
                    op = 'OTL' if st == 'set' else 'OTU' if st == 'reset' else 'OTE'
                    logic.append(((int(lid), 1), f"{op}({var}) := {drv} ;"))
                continue
            typ = e.get('typeName')
            inst = e.get('instanceName')
            qv = f"{inst}_Q"
            self.extra_locals.add(qv)
            if typ in ('TON', 'TOF', 'TP'):
                pt = self.in_int(e, 'PT', self.default_pt)
                self.timers.append({'id': qv, 'kind': typ, 'pt': pt})
                logic.append(((int(lid), 1),
                              f"{typ}({qv}, {pt}, {self.in_expr(e, 'IN') or 'TRUE'}) ;"))
            elif typ in ('CTU', 'CTD'):
                pv = self.in_int(e, 'PV', self.default_pt)
                a, b = ('CU', 'R') if typ == 'CTU' else ('CD', 'LD')
                self.counters.append({'id': qv, 'kind': typ, 'pv': pv})
                logic.append(((int(lid), 1),
                              f"{typ}({qv}, {pv}, {self.in_expr(e, a) or 'TRUE'}, "
                              f"{self.in_expr(e, b) or 'TRUE'}) ;"))
            elif typ in ('R_TRIG', 'F_TRIG'):
                clksig, prevv = f"{inst}_clk", f"prev_{inst}"
                self.extra_locals.update({clksig, prevv})
                clk = self.in_expr(e, 'CLK') or 'TRUE'
                # compute CLK, then the edge, in program order at this block:
                logic.append(((int(lid), 0), f"OTE({clksig}) := {clk} ;"))
                if typ == 'R_TRIG':
                    logic.append(((int(lid), 1),
                                  f"OTE({qv}) := XIC({clksig}) * XIO({prevv}) ;"))
                else:
                    logic.append(((int(lid), 1),
                                  f"OTE({qv}) := XIO({clksig}) * XIC({prevv}) ;"))
                fb_post.append(f"OTE({prevv}) := XIC({clksig}) ;")

        prelude, postlude = [], list(fb_post)
        for var, kinds in sorted(self.edges.items()):
            self.extra_locals.add('prev_' + var)
            if 'rising' in kinds:
                prelude.append(f"OTE(rise_{var}) := XIC({var}) * XIO(prev_{var}) ;")
            if 'falling' in kinds:
                prelude.append(f"OTE(fall_{var}) := XIO({var}) * XIC(prev_{var}) ;")
            postlude.append(f"OTE(prev_{var}) := XIC({var}) ;")

        program = prelude + [ln for _, ln in sorted(logic)] + postlude
        return program


def main():
    path = sys.argv[1]
    default_pt = int(os.environ.get('KLD_DEFAULT_PT', '2'))
    g = G(path, default_pt)
    program = g.build()
    print("\n".join(program))
    if len(sys.argv) > 2:
        fb_ids = {t['id'] for t in g.timers} | {c['id'] for c in g.counters}
        locals_ = [v for v, k in g.kinds.items() if k == 'local' and v not in fb_ids]
        locals_ += sorted(g.extra_locals - set(g.kinds))
        json.dump({'kinds': g.kinds,
                   'inputs':  [v for v, k in g.kinds.items() if k == 'input'],
                   'outputs': [v for v, k in g.kinds.items() if k == 'output'],
                   'locals':  locals_,
                   'timers':  g.timers,
                   'counters': g.counters},
                  open(sys.argv[2], 'w'), indent=2)


if __name__ == '__main__':
    main()
