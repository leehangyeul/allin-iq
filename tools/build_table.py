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
