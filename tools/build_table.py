# builds table/index.html (GTO 홀덤 테이블) from the claude.ai 'GTO 홀덤 테이블' file:
#   engine (Game, solver, charts, data) as is + per-seat villain styles, difficulty (admin), carried-over hero stack
#   + new ALLIN IQ screen (tools/table/shell.html + tools/table/ui.js): no hints, account stack, bust screen
# usage: python3 tools/build_table.py <gtt.html> [<site folder, default: repo root>]
import sys, os, re
SRC = sys.argv[1]
SITE = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(SRC, encoding='utf8').read()

# ---- the two scripts after the page markup: engine, then data + old screen
i0 = src.index('<div class="toast" id="toast" hidden></div>')
a = src.index('<script>\n', i0) + len('<script>\n'); b = src.index('</script>', a)
eng = src[a:b]
c = src.index('<script>\n', b) + len('<script>\n'); d = src.index('\nconst $ = id =>', c)
data = src[c:d]
assert data.startswith('const DATA') and 'const ENGINE_SRC' in data and 'loadEq(DATA.eq)' in data

def rep(o, n, cnt=1):
    global eng
    assert eng.count(o) == cnt, (eng.count(o), o[:90]); eng = eng.replace(o, n)
def rep_nth(o, news):
    global eng
    assert eng.count(o) == len(news), (eng.count(o), o[:90])
    for n in news: eng = eng.replace(o, n, 1)

# per-seat villain style: settings.styles = { pos: 'gto' | 'aggro' | ... }
rep("style() { return this.st.villain === 'custom' ? { ...VILLAIN_STYLES.gto, ...this.st.custom } : VILLAIN_STYLES[this.st.villain] || VILLAIN_STYLES.gto; }",
    "style(pos) { const k = (pos && this.st.styles && this.st.styles[pos]) || this.st.villain; return k === 'custom' ? { ...VILLAIN_STYLES.gto, ...this.st.custom } : VILLAIN_STYLES[k] || VILLAIN_STYLES.gto; }")
rep("const x = this.rng(), lm = st.loose;", "const st = this.style(pos), x = this.rng(), lm = st.loose;")
rep("const x = this.rng();\n          act = x < tb * st.aggr", "const x = this.rng(), st = this.style(pos);\n          act = x < tb * st.aggr")
rep("{ const x = this.rng(); resp = x < f4 * st.aggr", "{ const x = this.rng(), st = this.style(opener); resp = x < f4 * st.aggr")
rep("{ const x = this.rng(); act = x < r * st.aggr", "{ const x = this.rng(), st = this.style('BB'); act = x < r * st.aggr")
rep("{ const x = this.rng(); resp = x < fj * st.aggr", "{ const x = this.rng(), st = this.style('SB'); resp = x < fj * st.aggr")
rep("} else act = this.botCall(ev) ? 'call' : 'fold';", "} else act = this.botCall(ev, pos) ? 'call' : 'fold';")
rep_nth("} else resp = this.botCall(ev) ? 'call' : 'fold';", ["} else resp = this.botCall(ev, o.pos) ? 'call' : 'fold';", "} else resp = this.botCall(ev, 'SB') ? 'call' : 'fold';"])
rep_nth("} else call = this.botCall(ev);", ["} else call = this.botCall(ev, d.pos);", "} else call = this.botCall(ev, 'BB');"])
rep("} else jam = this.botCall(ev);", "} else jam = this.botCall(ev, d.pos);")
rep("} else call = this.botCall(ev2);", "} else call = this.botCall(ev2, o.pos);")
rep("botCall(ev) { const edge = this.style().callEdge || 0;", "botCall(ev, pos) { const edge = this.style(pos).callEdge || 0;")
assert 'this.botCall(ev)' not in eng and 'this.botCall(ev2)' not in eng
# postflop: the acting villain's style; difficulty (admin): settings.noise = share of a uniform mix (0 = solver strategy)
rep("probs = this.applyStyle(node.acts, probs);", "probs = this.applyStyle(node.acts, probs, actor.pos);")
rep("applyStyle(acts, probs) {\n    const st = this.style();", "applyStyle(acts, probs, pos) {\n    const st = this.style(pos), mix = +this.st.noise || 0;")
rep("    const s = out.reduce((a, b) => a + b, 0);\n    return s > 0 ? out.map(x => x / s) : probs;",
    "    const s = out.reduce((a, b) => a + b, 0);\n    const base = s > 0 ? out.map(x => x / s) : probs;\n    return mix > 0 ? base.map(x => x * (1 - mix) + mix / base.length) : base;")
# hero stack carried over between hands (account stack)
rep("if (S.stackMode !== 'mixed' || pos === heroPos) return stack;",
    "if (pos === heroPos) return S.heroStack != null ? S.heroStack : stack; if (S.stackMode !== 'mixed') return stack;")

# ---- free bet sizing after the flop (11/9): a size that is not in the solver tree re-solves the rest of the street from that spot
# with the hero's size added (subgame), so the villain's answer and the grading both use the real amount
SOLVER_PATCH = [
  ("this.root = this.build({ street: this.street, c: [0, 0], base: 0, toAct: 0, raises: 0, checked: false, board: this.board.slice() });",
   "const rs = cfg.rootState; this.root = this.build(rs ? { street: this.street, c: rs.c.slice(), base: rs.base || 0, toAct: rs.toAct, raises: rs.raises || 0, checked: !!rs.checked, board: this.board.slice(), extra: rs.extra } : { street: this.street, c: [0, 0], base: 0, toAct: 0, raises: 0, checked: false, board: this.board.slice() });"),
  ("  build(st) {\n    const { c, base, toAct } = st;",
   "  build(st) {\n    const extra = st.extra; if (extra != null) st = { ...st, extra: null };\n    const { c, base, toAct } = st;"),
  ("    const node = { t: 'A', p: toAct, acts, ch: [], c0: c[0], c1: c[1], street: st.street, board: st.board };",
   "    if (extra != null) addAct(facing <= 1e-9 ? 'bet' : 'raise', extra);\n    const node = { t: 'A', p: toAct, acts, ch: [], c0: c[0], c1: c[1], street: st.street, board: st.board, base: st.base, raises: st.raises, checked: st.checked };"),
]
for o_, n_ in SOLVER_PATCH: rep(o_, n_)
import json as _json
_i = data.index('const ENGINE_SRC = "'); _j = data.index('\n', _i)
_lit = data[_i + len('const ENGINE_SRC = '):_j].rstrip(';')
_src = _json.loads(_lit)
for o_, n_ in SOLVER_PATCH:
    assert _src.count(o_) == 1, o_[:60]; _src = _src.replace(o_, n_)
data = data[:_i] + 'const ENGINE_SRC = ' + _json.dumps(_src) + ';' + data[_j:]
# Game.postflop: hero sizing info + re-solve when the hero's size is new
rep("      const d = new _G.DistSolver(cfg, io.endpoints || []);\n      await d.init();", "      let d = new _G.DistSolver(cfg, io.endpoints || []);\n      await d.init();")
rep("      const m = d.master;\n      // 스트리트 레인지 정보", "      let m = d.master;\n      // 스트리트 레인지 정보")
rep("      const path = [];\n      let node = m.root;", "      let path = [];\n      let node = m.root;")
rep("""          const q = await d.query(path);
          const hi = m.handIndex(node.p, cfg.forceCombos[node.p]);
          const opts = node.acts.map((ac, k) => ({ label: this.actLabel(ac, node, actor), kind: ac.k, freq: q.strat[k * q.n + hi], ev: q.evA[k][hi] }));""",
"""          let q = await d.query(path);
          let hi = m.handIndex(node.p, cfg.forceCombos[node.p]);
          const mkOpts = () => node.acts.map((ac, k) => ({ label: this.actLabel(ac, node, actor), kind: ac.k, freq: q.strat[k * q.n + hi], ev: q.evA[k][hi] }));
          let opts = mkOpts();""")
rep("""          a = await io.heroAction({ street: h.street, options: opts.map(o => ({ label: o.label, kind: o.kind, freq: o.freq, ev: o.ev })), hud, pot: this.potTotal() });""",
"""          a = await io.heroAction({ street: h.street, options: opts.map(o => ({ label: o.label, kind: o.kind, freq: o.freq, ev: o.ev })), hud, pot: this.potTotal(), sizing: this.sizing(node) });
          if (a && typeof a === 'object') {
            const agg = ac => ac.k === 'bet' || ac.k === 'raise' || ac.k === 'allin';
            const X = Math.min(+a.to, h.streetStack), tol = Math.max(0.05, 0.02 * (h.streetStartPot + node.c0 + node.c1));
            let k = node.acts.findIndex(ac => agg(ac) && Math.abs(ac.to - X) <= tol);
            if (k < 0) {
              const cfg2 = { ...cfg, turnCards: h.street === 'flop' ? Math.min(cfg.turnCards || 99, PRECISION.normal.turnCards) : cfg.turnCards, ranges: m.rangesAfter(path), rootState: { c: [node.c0, node.c1], base: node.base || 0, toAct: node.p, raises: node.raises || 0, checked: !!node.checked, extra: X } };
              const d2 = new _G.DistSolver(cfg2, io.endpoints || []);
              await d2.init();
              io.solving({ street: h.street, iter: 0, maxIter: prec.maxIter, expl: null, ms: 0, done: false, custom: true });
              await d2.solve({ maxIter: prec.maxIter, targetPct: prec.targetPct, checkEvery: 10, onProgress: p => io.solving({ street: h.street, ...p, done: false, custom: true }) });
              io.solving({ street: h.street, iter: d2.master.iter, maxIter: prec.maxIter, done: true, custom: true });
              await d.dispose(); d = d2; m = d2.master; path = []; node = m.root;
              q = await d.query(path); hi = m.handIndex(node.p, cfg.forceCombos[node.p]); opts = mkOpts();
              k = node.acts.findIndex(ac => agg(ac) && Math.abs(ac.to - X) <= 1e-6);
              if (k < 0) k = node.acts.findIndex(ac => agg(ac) && Math.abs(ac.to - X) <= tol);
              h.resolves = (h.resolves || 0) + 1;
            }
            a = Math.max(0, k);
          }""")
rep("""  applyStyle(acts, probs, pos) {""","""  // 히어로가 직접 정하는 베팅·레이즈 크기 (이번 스트리트 총액 기준 to)
  sizing(node) {
    const h = this.hand, me = node.p, cMe = me === 0 ? node.c0 : node.c1, cOp = me === 0 ? node.c1 : node.c0, S = h.streetStack;
    const agg = node.acts.filter(ac => ac.k === 'bet' || ac.k === 'raise' || ac.k === 'allin');
    if (!agg.length || cMe >= S - 1e-9) return null;
    const facing = cOp - cMe, pot = h.streetStartPot + node.c0 + node.c1;
    const min = facing > 1e-9 ? Math.min(S, 2 * cOp - cMe) : Math.min(S, cMe + 1);
    return { kind: facing > 1e-9 ? 'raise' : 'bet', me: cMe, opp: cOp, facing, pot, min, max: S, def: agg[0].to, tree: agg.map(ac => ac.to) };
  }
  applyStyle(acts, probs, pos) {""")

# ---- texts: no source names, no prize words (ICM is off here: stage is always 'early')
eng = '\n'.join(l for l in eng.split('\n') if not (l.lstrip().startswith('//') and re.search(r'Little|Jonathan|Wizard|Negreanu|PokerCoaching|상금|강의|교재', l)))
rep(" (Little·Negreanu 공통).", ".")
rep(" (Easy Game의 베팅 이유 1).", ".")
rep(", Little 예시와 비슷)", ")")
eng = eng.replace('상금', '지급')
for w in ['Little', 'Jonathan', 'Wizard', 'Negreanu', 'PokerCoaching', '상금', '현금', '경품', '환전']:
    assert w not in eng, w

shell = open(os.path.join(HERE, 'table', 'shell.html'), encoding='utf8').read()
ui = open(os.path.join(HERE, 'table', 'ui.js'), encoding='utf8').read()
out = shell.replace('<!--ENGINE-->', '<script>\n' + eng + '\n</script>').replace('<!--UI-->', '<script>\n' + data + '\n' + ui + '\n</script>')
for w in ['상금', '현금', '경품', '환전', 'Little', 'Wizard']:
    assert w not in out.replace(data, ''), w
os.makedirs(os.path.join(SITE, 'table'), exist_ok=True)
open(os.path.join(SITE, 'table', 'index.html'), 'w', encoding='utf8').write(out)
print('table/index.html', len(out))
