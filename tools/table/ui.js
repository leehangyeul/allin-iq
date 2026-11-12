// ===== ALLIN IQ · GTO 홀덤 테이블 화면 (11/9) =====
// 엔진(Game·솔버)은 GTO 홀덤 테이블 그대로. 여기서는: 내 계정 스택 이어가기(다 잃으면 탈락), 빌런 8명 성향, 힌트 없는 화면, 결과·통계·탈락 화면.
const $ = id => document.getElementById(id);
const SUITSYM = ['♣', '♦', '♥', '♠'], SUITCLS = ['c', 'd', 'h', 's'];
const fmt = (x, d = 1) => (x == null || !isFinite(x)) ? '–' : (+x).toFixed(d);
const sgn = x => (x > 0 ? '+' : x < 0 ? '−' : '') + Math.abs(+x).toFixed(1);
const pct = x => x == null || !isFinite(x) ? '–' : (x * 100).toFixed(x > 0 && x < 0.1 ? 1 : 0) + '%';
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const BBu = t => String(t).replace(/(\d+(?:\.\d+)?)(?:bb)?(?=$|[\s)·,])/g, (m, n, off, str) => { const p = str[off - 1]; return (p === ':' || p === '.' || (p >= '0' && p <= '9')) ? m : n + 'BB'; });
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
};

// ---------- 계정 연결: 앱 안에서는 앱(GT_STORE)이 내 계정에 저장, 단독으로 열면 이 기기에만 ----------
const PS = (() => { try { return window.parent !== window && window.parent.GT_STORE ? window.parent.GT_STORE : null; } catch (e) { return null; } })();
const ST = PS || {
  who: () => ({ ok: true, name: '', local: true }),
  cfg: () => window.__GT_TEST_CFG || ({}),
  async load() { return store.get('gt_acct_v1', null); },
  async save(d) { store.set('gt_acct_v1', d); return true; },
  quiz() { location.href = '../'; }, join() { location.href = '../'; },
};
const CFG_DEF = { start: 40, regrant: 'day', prec: 'precise', diff: 'hard' };
const cfg = () => { const c = Object.assign({}, CFG_DEF, (ST.cfg && ST.cfg()) || {}); if (![20, 40, 60, 100].includes(+c.start)) c.start = 40; c.start = +c.start; return c; };
// 난이도(관리자만): 빌런이 솔버 전략에서 벗어나는 정도. 어려움 = 솔버 전략 그대로
const NOISE = { hard: 0, mid: 0.15, easy: 0.3 };
const STYLE_KEYS = ['gto', 'aggro', 'passive', 'station', 'nit'];
const STYLE_DOT = { gto: '#D4AF7C', aggro: '#F08A80', passive: '#7FB3F0', station: '#7FD4A0', nit: '#B9A2E8' };
const ROT = ['BB', 'SB', 'BTN', 'CO', 'HJ', 'LJ', 'UTG2', 'UTG1', 'UTG']; // 버튼이 한 칸씩 돌 때 내 자리
const SEAT_ORDER = ['UTG', 'UTG1', 'UTG2', 'LJ', 'HJ', 'CO', 'BTN', 'SB', 'BB']; // 시계방향
const heroPosFor = n => ROT[((n % 9) + 9) % 9];
const villainPos = (heroPos, k) => SEAT_ORDER[(SEAT_ORDER.indexOf(heroPos) + k) % 9]; // 빌런 k = 내 왼쪽부터 k번째

const DAY = 864e5, KST = 9 * 36e5;
const kday = t => Math.floor((t + KST) / DAY);
const ymd = t => { const d = new Date(t + KST); return d.getUTCFullYear() * 10000 + (d.getUTCMonth() + 1) * 100 + d.getUTCDate(); };
function nextGrant(bust, mode) {
  if (!bust) return 0;
  if (mode === 'admin') return Infinity;
  const d = kday(bust);
  if (mode === 'week') { const dow = (d + 4) % 7; return (d + ((8 - dow) % 7 || 7)) * DAY - KST; } // 다음 월요일 0시
  return (d + 1) * DAY - KST; // 다음 날 0시
}
function grantText(t) {
  if (t === Infinity) return '관리자가 줄 때';
  const dd = kday(t) - kday(Date.now());
  if (dd <= 0) return '지금';
  if (dd === 1) return '내일 0시';
  const x = new Date(t + KST);
  return `${x.getUTCMonth() + 1}/${x.getUTCDate()}(${'일월화수목금토'[x.getUTCDay()]}) 0시`;
}

let A = null;           // 내 계정 기록 { s 스택, h 이번 판 핸드, best, ev, dn, good, life 판 수, lh 탈락한 판의 핸드 합, bn 탈락 수, bust, day, dh, th, st[8], name, at }
let settings = Object.assign(defaultSettings(), { maxRaises: 3 });
const n0 = v => (typeof v === 'number' && isFinite(v) && v >= 0) ? v : 0;
function fresh(prev) {
  const c = cfg();
  return { name: (ST.who().name || '').slice(0, 12), s: c.start, h: 0, best: c.start, ev: 0, dn: 0, good: 0, life: n0(prev && prev.life) + 1, lh: n0(prev && prev.lh), bn: n0(prev && prev.bn), bust: 0,
    day: n0(prev && prev.day), dh: n0(prev && prev.dh), th: n0(prev && prev.th), st: (prev && Array.isArray(prev.st) ? prev.st : []).slice(0, 8), at: Date.now() };
}
function clean(d) {
  const o = {}; for (const k of ['s', 'h', 'best', 'ev', 'dn', 'good', 'life', 'lh', 'bn', 'bust', 'day', 'dh', 'th']) o[k] = n0(d[k]);
  o.st = (Array.isArray(d.st) ? d.st : []).slice(0, 8).map(x => STYLE_KEYS.includes(x) ? x : 'gto');
  o.name = String(d.name || ST.who().name || '').slice(0, 12); o.at = n0(d.at);
  return o;
}
const styles8 = () => { const s = (A && A.st) || []; return Array.from({ length: 8 }, (_, i) => STYLE_KEYS.includes(s[i]) ? s[i] : 'gto'); };
let saveT = null, saving = Promise.resolve();
const bkKey = () => { const w = ST.who(); return 'gt_acct_bk_' + (w.uid || w.name || 'me'); };
let srvWarned = false;
function srvWarn() { if (srvWarned) return; srvWarned = true; toast('내 계정에 아직 저장되지 않아 이 기기에 저장해 두고 있어요. 연결되면 계정으로 옮겨요.', 4500); }
function saveNow() {
  clearTimeout(saveT); saveT = null; if (!A) return saving;
  A.at = Date.now(); A.name = (ST.who().name || A.name || '').slice(0, 12); A.st = styles8();
  const snap = JSON.parse(JSON.stringify(A));
  if (PS) store.set(bkKey(), snap);
  saving = saving.then(() => ST.save(snap)).catch(e => { console.warn(e); srvWarn(); });
  return saving;
}
function saveSoon() { clearTimeout(saveT); saveT = setTimeout(saveNow, 700); }
async function loadAcct() {
  let d, bk = PS ? store.get(bkKey(), null) : null;
  try { d = await ST.load(); } catch (e) { console.warn(e); d = null; srvWarn(); }
  let fromBk = false;
  if (bk && typeof bk.s === 'number' && (!d || typeof d.s !== 'number' || (+bk.at || 0) > (+d.at || 0))) { d = bk; fromBk = true; } // 계정에 못 올린 최신 기록
  const c = cfg();
  if (!d || typeof d.s !== 'number') { A = fresh(null); await saveNow(); return true; }
  A = clean(d);
  if (fromBk) saveNow();
  if (A.s <= 0 && Date.now() >= nextGrant(A.bust || Date.now(), c.regrant)) { A = fresh(A); await saveNow(); }
  return true;
}

// ---------- 솔버 워커 ----------
function makeEndpoints() {
  // 워커 하나가 정밀 모드에서 메모리를 약 80MB 써요(6개면 페이지가 760MB까지 커져 오래된 휴대폰에서 꺼질 수 있음) → 4개까지, 메모리 3GB 이하 기기는 2개
  const mem = +navigator.deviceMemory || 8, cap = mem <= 3 ? 2 : 4;
  const n = Math.max(1, Math.min(cap, (navigator.hardwareConcurrency || 4) - 1));
  const eps = [];
  try {
    const src = ENGINE_SRC + '\nconst __h = makeWorkerHandler();\nself.onmessage = e => { const { id, type, payload } = e.data; try { self.postMessage({ id, result: __h(type, payload) }); } catch (err) { self.postMessage({ id, error: String(err && err.stack || err) }); } };';
    const url = URL.createObjectURL(new Blob([src], { type: 'text/javascript' }));
    for (let i = 0; i < n; i++) {
      const w = new Worker(url); let seq = 0; const pend = new Map();
      w.onmessage = e => { const m = e.data, p = pend.get(m.id); if (!p) return; pend.delete(m.id); m.error ? p.rej(new Error(m.error)) : p.res(m.result); };
      w.onerror = () => { for (const p of pend.values()) p.rej(new Error('worker error')); pend.clear(); };
      eps.push({ call(type, payload) { const id = ++seq; return new Promise((res, rej) => { pend.set(id, { res, rej }); w.postMessage({ id, type, payload }); }); } });
    }
  } catch (e) { console.warn('워커 사용 불가, 메인 스레드에서 계산', e); return []; }
  return eps;
}

// ---------- 카드·테이블 ----------
function cardEl(c, cls = '') {
  const d = document.createElement('div');
  if (c == null) { d.className = 'card back ' + cls; return d; }
  const r = RANK_CH[c >> 2], s = c & 3;
  d.className = 'card ' + SUITCLS[s] + ' ' + cls;
  d.innerHTML = (r === 'T' ? '10' : r) + '<i>' + SUITSYM[s] + '</i>';
  return d;
}
const cardTxt = c => RANK_CH[c >> 2] + SUITSYM[c & 3];
function kindOf(o) { const k = o.kind || o.k || ''; if (k === 'jam' || k === 'allin' || /올인/.test(o.label || '')) return 'allin'; if (k === 'fold') return 'fold'; if (k === 'bet' || k === 'raise' || k === '3bet') return 'bet'; return 'call'; }
const KCOLOR = { fold: '#5B6170', call: '#7FB3F0', bet: '#D4AF7C', allin: '#C2474F' };
function seatXY(k) { const ang = Math.PI / 2 + k * (2 * Math.PI / 9); return { x: 50 + 44 * Math.cos(ang), y: 47 + 39 * Math.sin(ang) }; }
let lastBoardLen = 0, betBase = {}, betBaseLen = -1;
function renderTable(v) {
  if (!v) return;
  // 앞에 놓인 칩 = 이번 스트리트에 건 금액 (프리플랍에 넣은 칩은 팟으로)
  if (v.board.length !== betBaseLen) { betBaseLen = v.board.length; betBase = {}; if (v.board.length) v.seats.forEach(s => betBase[s.pos] = s.inv); }
  const streetBet = s => Math.max(0, s.inv - (betBase[s.pos] || 0));
  const heroIdx = SEAT_ORDER.indexOf(v.heroPos);
  const el = $('seats'); el.innerHTML = '';
  const sty = settings.styles || {};
  const TW = $('table').clientWidth, TH = $('table').clientHeight;
  v.seats.forEach(s => {
    const k = (SEAT_ORDER.indexOf(s.pos) - heroIdx + 9) % 9;
    if (s.hero) return;
    const { x, y } = seatXY(k);
    const d = document.createElement('div');
    d.className = 'seat' + (s.folded ? ' folded' : '') + (s.inHand ? ' inhand' : '') + (v.toAct === s.pos ? ' acting' : '');
    d.style.left = x + '%'; d.style.top = y + '%';
    if (s.cards && v.result) { const cs = document.createElement('div'); cs.className = 'cards'; s.cards.forEach(c => cs.appendChild(cardEl(c))); d.appendChild(cs); }
    else if (s.inHand && !s.folded) { const cs = document.createElement('div'); cs.className = 'cards'; cs.appendChild(cardEl(null)); cs.appendChild(cardEl(null)); d.appendChild(cs); }
    const st = sty[s.pos] || 'gto';
    const box = document.createElement('div'); box.className = 'box';
    box.innerHTML = `<div class="pos"><span class="dot" style="background:${STYLE_DOT[st]}"></span>${POS_KO[s.pos]}</div><div class="stk">${fmt(s.stack)}</div>`;
    if (v.villain === s.pos) { const t = document.createElement('div'); t.className = 'tag'; t.textContent = '빌런'; box.prepend(t); }
    d.appendChild(box);
    if (s.lastAct) { const a = document.createElement('div'); a.className = 'act'; a.textContent = BBu(s.lastAct); if (y < 30) d.prepend(a); else d.appendChild(a); }
    el.appendChild(d);
    // 앞 칩: 좁은 화면(테이블 420px 미만)에선 자리 글씨(예: 벳 2.1BB)가 같은 금액을 보여 주니 생략, 넓은 화면에선 자리 바로 바깥(가운데 쪽)에
    if (streetBet(s) > 0.001 && !v.result && TW >= 420) {
      const sx = x / 100 * TW, sy = y / 100 * TH; let dx = TW / 2 - sx, dy = 0.47 * TH - sy; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
      const t = Math.min(dx ? d.offsetWidth / 2 / Math.abs(dx) : 1e9, dy ? d.offsetHeight / 2 / Math.abs(dy) : 1e9) + 14;
      const b = document.createElement('div'); b.className = 'bet'; b.style.left = ((sx + dx * t) / TW * 100) + '%'; b.style.top = ((sy + dy * t) / TH * 100) + '%'; b.textContent = fmt(streetBet(s)); el.appendChild(b);
    }
    if (s.pos === 'BTN') { const m = document.createElement('div'); m.className = 'btnmark'; m.textContent = 'D'; m.style.left = (x + (50 - x) * 0.3) + '%'; m.style.top = (y + (47 - y) * 0.3 - 6) + '%'; el.appendChild(m); }
  });
  const hero = v.seats.find(s => s.hero);
  const hh = document.createElement('div'); hh.className = 'herohand';
  (hero.cards || [null, null]).forEach(c => hh.appendChild(cardEl(c, 'big')));
  el.appendChild(hh);
  const hb = document.createElement('div'); hb.className = 'herobar';
  hb.innerHTML = `<span>히어로 ${POS_KO[v.heroPos]}${hero.pos === 'BTN' ? ' · D' : ''}</span><b>${fmt(hero.stack)}<small style="font-size:11px">BB</small></b>${streetBet(hero) > 0.001 && !v.result ? `<small class="mono" style="color:var(--gold-2)">베팅 ${fmt(streetBet(hero))}</small>` : ''}`;
  el.appendChild(hb);
  const bd = $('board'); bd.innerHTML = '';
  for (let i = 0; i < 5; i++) {
    if (i < v.board.length) bd.appendChild(cardEl(v.board[i], i >= lastBoardLen ? 'deal' : ''));
    else { const s = document.createElement('div'); s.className = 'slot'; bd.appendChild(s); }
  }
  lastBoardLen = v.board.length;
  $('pot').textContent = fmt(v.pot) + 'BB';
  $('h-pot').textContent = fmt(v.pot) + 'BB';
  if (v.spr != null && !v.result) $('h-spr').textContent = fmt(v.spr, 1);
}
function renderLog(v) {
  const el = $('log'); el.innerHTML = '';
  (v ? v.log : []).forEach(l => {
    const d = document.createElement('div');
    if (!l.pos) { d.className = 't'; d.textContent = BBu(l.text); }
    else d.innerHTML = `<span class="p">${POS_KO[l.pos]}</span><span class="${l.hero ? 'h' : ''}">${l.hero ? '히어로 · ' : ''}${esc(BBu(l.text))}</span>`;
    el.appendChild(d);
  });
  el.scrollTop = el.scrollHeight;
}
function renderHud(hud) {
  $('h-eff').textContent = hud && hud.eff != null ? fmt(hud.eff) + 'BB' : '–';
  $('h-spr').textContent = hud && hud.spr != null ? fmt(hud.spr, 1) : '–';
}
function renderChips() {
  const c = cfg();
  $('c-stack').textContent = A ? fmt(A.s) + 'BB' : '–';
  $('c-hands').textContent = A ? A.h : 0;
  $('c-loss').textContent = A ? fmt(A.ev, 1) : '0';
  $('sub').textContent = `9인 MTT · 시작 ${c.start}BB · 헤즈업 포스트플랍`;
}

// ---------- 액션 (힌트 없음) ----------
let pendingAction = null;
function splitLabel(o) {
  let l = BBu(o.label).replace(/^벳 /, '베팅 ');
  const i = l.indexOf(' (');
  if (i < 0) return [l, ''];
  return [l.slice(0, i), l.slice(i + 2).replace(/\)$/, '').replace(/^(\d+%)$/, '팟 $1')];
}
function lastVillainAct() {
  const v = lastView; if (!v) return '';
  for (let i = v.log.length - 1; i >= 0; i--) { const l = v.log[i]; if (l.pos && !l.hero) return `${POS_KO[l.pos]} ${BBu(l.text)}`; if (l.pos && l.hero) return ''; }
  return '';
}
function showActions(info) {
  $('waiting').hidden = true;
  const la = lastVillainAct();
  $('status').innerHTML = la ? `<em>${esc(la)}</em> → 히어로 차례` : '히어로 차례';
  const box = $('actions'); box.innerHTML = ''; $('sizer').hidden = true; $('sizer').innerHTML = '';
  const pick = v => { if (!pendingAction) return; const r = pendingAction; pendingAction = null; box.innerHTML = ''; $('sizer').hidden = true; $('sizer').innerHTML = ''; $('status').textContent = ''; wait('진행 중…'); r(v); };
  if (info.sizing) return showSizer(info, pick);
  info.options.forEach((o, i) => {
    const [main, sub] = splitLabel(o);
    const b = document.createElement('button'); b.type = 'button';
    b.id = 'act-' + i; b.className = 'k-' + kindOf(o);
    b.innerHTML = `<span>${esc(main)}</span>${sub ? `<small>${esc(sub)}</small>` : ''}`;
    b.onclick = () => pick(i);
    box.appendChild(b);
  });
}
// 플랍부터: 베팅·레이즈 크기를 BB로 직접 정해요 (−/+ · 슬라이더 · 1/3~팟·올인). 솔버 기본 크기가 아니면 그 크기로 다시 계산해요.
const r1 = x => Math.round(x * 10) / 10;
function showSizer(info, pick) {
  const z = info.sizing, box = $('actions'), el = $('sizer');
  const isRaise = z.kind === 'raise', word = isRaise ? '레이즈' : '베팅';
  const min = r1(Math.min(z.max, Math.max(z.min, 0.1))), max = r1(z.max);
  const clamp = v => { v = r1(v); if (!(v >= min)) v = min; if (v > max) v = max; return v; };
  const presetTo = f => isRaise ? z.opp + f * (z.pot + z.facing) : z.me + f * z.pot;
  const potPct = to => isRaise ? (to - z.opp) / Math.max(0.01, z.pot + z.facing) : (to - z.me) / Math.max(0.01, z.pot);
  let val = clamp(z.def);
  const P = [['1/3', 1 / 3], ['1/2', 0.5], ['2/3', 2 / 3], ['3/4', 0.75], ['팟', 1], ['올인', null]];
  el.hidden = false;
  el.innerHTML = `<div class="szhd"><span class="szl">${word} 크기</span><span id="sz-pct"></span></div>
    <div class="szrow"><button type="button" class="szb" id="sz-m" aria-label="줄이기">−</button>
      <label class="szv"><input id="sz-in" type="number" inputmode="decimal" step="0.1" min="${min}" max="${max}" aria-label="${word} 크기 BB"><span>BB</span></label><button type="button" class="szb" id="sz-p" aria-label="늘리기">＋</button></div>
    <input id="sz-r" type="range" min="${min}" max="${max}" step="0.1" aria-label="${word} 크기 슬라이더">
    <div class="szlb"><span>최소 ${fmt(min)}BB</span><span>올인 ${fmt(max)}BB</span></div>
    <div class="szps">${P.map(([t, f], i) => `<button type="button" data-p="${i}">${t}</button>`).join('')}</div>
    <p class="note" style="text-align:left">${isRaise ? '레이즈는 이번 스트리트 총액이에요. ' : ''}솔버 기본 크기와 다르면 그 크기로 다시 계산해서 빌런이 대응해요${info.street === 'flop' ? '(플랍은 10~30초 더 걸려요)' : ''}.</p>`;
  const inp = $('sz-in'), rg = $('sz-r');
  const btns = [];
  info.options.forEach((o, i) => { const k = o.kind; if (k === 'fold' || k === 'check' || k === 'call') { const [main, sub] = splitLabel(o); const b = document.createElement('button'); b.type = 'button'; b.id = 'act-' + i; b.className = 'k-' + kindOf(o); b.innerHTML = `<span>${esc(main)}</span>${sub ? `<small>${esc(sub)}</small>` : ''}`; b.onclick = () => pick(i); btns.push(b); } });
  const go = document.createElement('button'); go.type = 'button'; go.id = 'act-size';
  go.onclick = () => pick({ to: val });
  btns.push(go); btns.forEach(b => box.appendChild(b));
  const show = (from) => {
    const all = val >= max - 1e-9;
    if (from !== 'in') inp.value = val.toFixed(1);
    if (from !== 'rg') rg.value = val;
    $('sz-pct').textContent = `팟의 ${Math.round(potPct(val) * 100)}%`;
    go.className = all ? 'k-allin' : 'k-bet';
    go.innerHTML = all ? `<span>올인 ${fmt(val)}BB</span>` : `<span>${word} ${fmt(val)}BB</span><small>팟의 ${Math.round(potPct(val) * 100)}%</small>`;
  };
  inp.oninput = () => { const v = parseFloat(inp.value); if (isFinite(v) && v >= min && v <= max) { val = r1(v); show('in'); } };
  inp.onchange = () => { val = clamp(parseFloat(inp.value)); show(); };
  rg.oninput = () => { val = clamp(parseFloat(rg.value)); show('rg'); };
  const step = () => val >= 20 ? 1 : 0.5;
  $('sz-m').onclick = () => { val = clamp(val - step()); show(); };
  $('sz-p').onclick = () => { val = clamp(val + step()); show(); };
  el.querySelectorAll('[data-p]').forEach(b => b.onclick = () => { const f = P[+b.dataset.p][1]; val = f == null ? max : clamp(presetTo(f)); show(); });
  show();
}
function wait(t) { const w = $('waiting'); w.hidden = !t; w.textContent = t || ''; }

// ---------- 시트·토스트 ----------
let sheetLocked = false;
function openSheet(html, onMount) { $('sheet-body').innerHTML = html; $('sheet').hidden = false; $('sheet-body').scrollTop = 0; if (onMount) onMount($('sheet-body')); }
function closeSheet() { $('sheet').hidden = true; $('sheet-body').innerHTML = ''; }
$('sheet').addEventListener('click', e => { if (e.target === $('sheet') && !sheetLocked) closeSheet(); });
function toast(text, ms = 2800) { const t = $('toast'); t.textContent = text; t.hidden = false; clearTimeout(toast._t); toast._t = setTimeout(() => t.hidden = true, ms); }

// ---------- 결과 화면 ----------
function decisionHtml(d) {
  const isPre = d.street === 'preflop';
  const hasEV = d.options.some(o => o.ev != null);
  const allEV = d.options.every(o => o.ev != null);
  const stName = { preflop: '프리플랍', flop: '플랍', turn: '턴', river: '리버' }[d.street];
  const gradeTxt = { good: '좋음', ok: '작은 실수', bad: '실수' }[d.grade];
  const rows = d.options.map((o, k) => {
    const loss = allEV ? Math.max(0, Math.max(...d.options.map(x => x.ev ?? -1e9)) - o.ev) : null;
    return `<div class="opt${k === d.chosen ? ' me' : ''}"><span class="nm"><i style="background:${KCOLOR[kindOf(o)]}"></i>${k === d.chosen ? '▶ ' : ''}${esc(splitLabel(o)[0])}</span><span class="r">${pct(o.freq)}</span><span class="r">${o.ev != null ? fmt(o.ev, 2) : ''}</span><span class="r" style="color:${loss > 0.05 ? 'var(--bad)' : 'var(--good)'}">${loss != null ? fmt(loss, 2) : ''}</span></div>`;
  }).join('');
  const bar = `<div class="fbar">${d.options.map(o => `<div style="width:${(o.freq || 0) * 100}%;background:${KCOLOR[kindOf(o)]}"></div>`).join('')}</div>`;
  const cardsHtml = !isPre ? `<span style="display:inline-flex;gap:3px;vertical-align:middle">${d.board.map(c => `<span class="mono" style="font-size:12px;padding:1px 4px;border-radius:4px;background:#FBF6EC;color:${(c & 3) === 1 || (c & 3) === 2 ? '#C2343F' : '#15171C'}">${cardTxt(c)}</span>`).join('')}</span>` : '';
  const sub = isPre ? `${esc(d.cls || '')} · ${esc(BBu(d.chartName || ''))}` : `팟 ${fmt(d.pot)}BB · SPR ${fmt(d.spr, 1)} · 솔버 계산`;
  const lossTxt = (!isPre || d.preEV || (d.evLoss || 0) > 0) ? ' · −' + fmt(d.evLoss, 2) : '';
  const notes = (d.notes || []).map(n => `<li><b>${esc(n.t)}</b> ${esc(BBu(n.d))}</li>`).join('');
  return `<div class="dec"><div class="head"><span><span class="st">${stName}</span> ${cardsHtml}</span><span class="grade ${d.grade}">${gradeTxt}${lossTxt}</span></div>
    <span class="meta">${sub}</span>${bar}<div class="opt hdr"><span>액션</span><span class="r">GTO</span><span class="r">${hasEV ? 'EV' : ''}</span><span class="r">${allEV ? '손실' : ''}</span></div>${rows}
    ${notes ? `<details class="coach"${d.grade !== 'good' ? ' open' : ''}><summary>코치 노트</summary><ul>${notes}</ul></details>` : ''}</div>`;
}
function handEndHtml(v, n) {
  const r = v.result;
  const reasonTxt = { showdown: '쇼다운', fold: '상대 폴드', herofold: '히어로 폴드', walk: 'BB 워크' }[r.reason] || '';
  const won = r.winner.includes(v.heroPos);
  let title = r.reason === 'herofold' ? '폴드했어요' : won ? (r.winner.length > 1 ? '팟을 나눴어요' : '이겼어요') : '졌어요';
  const loss = v.decisions.reduce((s, d) => s + (d.evLoss || 0), 0);
  const good = v.decisions.filter(d => d.grade !== 'bad').length;
  const me = v.seats.find(s => s.hero);
  return `<div class="sheethead"><div><h2>핸드 결과</h2><span class="meta">GTO 홀덤 테이블 · 핸드 #${n}</span></div></div>
    <div class="res"><div class="row"><span class="net ${r.net > 0 ? 'pos' : r.net < 0 ? 'neg' : ''}">${sgn(r.net)}BB</span><span class="meta">${title} · ${reasonTxt}</span></div>
      <div class="row"><span class="badge">이 핸드 EV 손실 ${fmt(loss, 2)}BB</span>${v.decisions.length ? `<span class="badge" style="background:rgba(127,212,160,.12);color:var(--good);border-color:rgba(127,212,160,.35)">GTO 일치 ${good}/${v.decisions.length}</span>` : ''}<span class="meta">내 스택 ${fmt(me.stack)}BB</span></div>
      <div class="vs"><div><div class="who">히어로 ${POS_KO[v.heroPos]}</div><div class="cards">${me.cards.map(c => cardEl(c).outerHTML).join('')}</div></div>
        ${v.villain ? `<div><div class="who">빌런 ${POS_KO[v.villain]}</div><div class="cards">${(v.villainCards && r.reason === 'showdown' ? v.villainCards : [null, null]).map(c => cardEl(c).outerHTML).join('')}</div></div>` : ''}
        ${v.board.length ? `<div><div class="who">보드</div><div class="cards">${v.board.map(c => cardEl(c).outerHTML).join('')}</div></div>` : ''}</div></div>
    ${v.decisions.map(decisionHtml).join('')}`;
}
let lastHand = null; // { v, n } 마지막 핸드 다시 보기
function showHandEnd(v, n, busted) {
  return new Promise(res => {
    sheetLocked = true;
    openSheet(handEndHtml(v, n) + `<button class="primary" id="sh-next" type="button">${busted ? '결과 보기' : '다음 핸드'}</button>`, b => {
      b.querySelector('#sh-next').onclick = () => { sheetLocked = false; closeSheet(); res(); };
    });
  });
}

// ---------- 게임 연결 ----------
let endpoints = null, game = null, running = false, lastView = null;
const savedStats = store.get('gt_stats_v1', null);
const io = {
  endpoints: [],
  render(v) {
    lastView = v; renderTable(v); renderLog(v);
    // 핸드 중 내가 넣은 칩은 바로 내 계정에서 빠져요(중간에 나가면 폴드와 같아요)
    const me = v && v.seats.find(s => s.hero);
    if (A && me && !v.result && me.stack < A.s - 0.004) { A.s = Math.max(0, Math.round(me.stack * 100) / 100); renderChips(); saveSoon(); }
  },
  log() {}, notice() {},
  wait(ms) { return new Promise(r => setTimeout(r, ms)); },
  solving(p) {
    const el = $('solve');
    if (p.done) { el.hidden = true; return; }
    el.hidden = false;
    const name = { flop: '플랍', turn: '턴', river: '리버' }[p.street];
    $('solve-t').textContent = p.custom ? `내 ${name} 베팅 크기로 다시 계산 ${p.iter}/${p.maxIter}` : `${name} 솔버 계산 ${p.iter}/${p.maxIter}`;
    $('solve-b').style.width = Math.min(100, p.iter / p.maxIter * 100) + '%';
    wait('솔버가 이 스팟을 푸는 중…');
  },
  heroAction(info) { renderHud(info.hud); return new Promise(res => { pendingAction = res; showActions(info); }); },
};
function prepHand() {
  const c = cfg();
  Object.assign(settings, { stack: c.start, stackMode: 'mixed', stage: 'early', feedback: 'end', ante: 1, villain: 'gto',
    precision: PRECISION[c.prec] ? c.prec : 'precise', noise: NOISE[c.diff] ?? 0, heroSeat: heroPosFor(A.th), heroStack: A.s, payouts: {} });
  const s8 = styles8(); settings.styles = {};
  for (let k = 1; k <= 8; k++) settings.styles[villainPos(settings.heroSeat, k)] = s8[k - 1];
}
function afterHand() {
  const h = game.hand, me = h.by[h.heroPos];
  let s = Math.round(me.stack * 100) / 100; if (s < 0.005) s = 0;
  const now = Date.now(), today = ymd(now);
  A.s = s; A.h++; A.th++;
  if (A.day !== today) { A.day = today; A.dh = 0; } A.dh++;
  A.best = Math.max(A.best, s);
  A.ev = Math.round((A.ev + h.decisions.reduce((t, d) => t + (d.evLoss || 0), 0)) * 1000) / 1000;
  A.dn += h.decisions.length; A.good += h.decisions.filter(d => d.grade !== 'bad').length;
  if (s <= 0) { A.bust = now; A.lh += A.h; A.bn++; }
  saveNow(); store.set('gt_stats_v1', game.stats); renderChips();
}
async function loop() {
  if (running || !A) return;
  if (A.s <= 0) { showBust(); return; }
  running = true; $('b-start').hidden = true;
  if (!endpoints) { endpoints = makeEndpoints(); io.endpoints = endpoints; }
  if (!game) { game = new Game(settings, { pushfold: DATA.pushfold }, io); if (savedStats) Object.assign(game.stats, savedStats); }
  while (running) {
    prepHand();
    const start = A.s;
    renderHud(null); $('status').textContent = ''; wait('카드를 나누는 중…');
    let res;
    try { res = await game.playHand(); }
    catch (e) { console.error(e); A.s = start; saveNow(); renderChips(); toast('오류가 나서 이 핸드를 건너뛰어요. 스택은 그대로예요.', 4000); await io.wait(800); continue; }
    afterHand();
    const v = game.view(), n = A.th, busted = A.s <= 0;
    lastHand = { v, n };
    renderHud(null); wait('');
    const pre = v.decisions.filter(d => d.street === 'preflop');
    if (!busted && res.reason === 'herofold' && v.decisions.length === 1 && pre[0] && pre[0].grade !== 'bad') { wait('폴드 — 다음 핸드'); await io.wait(700); continue; }
    if (!busted && !v.decisions.length && res.reason !== 'walk') { await io.wait(500); continue; }
    await showHandEnd(v, n, busted);
    if (busted) { running = false; showBust(); return; }
  }
}
$('b-start').onclick = loop;

// ---------- 탈락 ----------
function showBust() {
  const c = cfg(), t = nextGrant(A.bust || Date.now(), c.regrant);
  $('main').hidden = true;
  const g = $('gate'); g.hidden = false; g.className = '';
  const acc = A.dn ? pct(A.good / A.dn) : '–';
  g.innerHTML = `<div class="bust"><div class="zero">0BB</div><h2>스택을 모두 잃었어요</h2><p>이번 판은 여기까지예요. ${A.h}핸드 동안 버텼어요.</p></div>
    <div class="statgrid">
      <div class="tile"><span>친 핸드</span><b>${A.h}</b></div><div class="tile"><span>최고 스택</span><b>${fmt(A.best)}BB</b></div><div class="tile hl"><span>EV 손실 합</span><b>${fmt(A.ev, 1)}</b></div>
      <div class="tile hl"><span>EV 손실 /100핸드</span><b>${A.h ? fmt(A.ev / A.h * 100, 1) : '–'}</b></div><div class="tile"><span>GTO 일치율</span><b>${acc}</b></div><div class="tile"><span>마지막 핸드</span><b>#${A.th}</b></div></div>
    <div class="nextbox"><div class="r"><span>다음 ${c.start}BB</span><b>${grantText(t)}</b></div>
      <p>탈락하면 다시 받을 때까지 칠 수 없어요(관리자가 정한 규칙: ${c.regrant === 'week' ? '매주 월요일 0시' : c.regrant === 'admin' ? '관리자가 줄 때' : '매일 0시'}에 새 ${c.start}BB). 그동안 핸드 퀴즈·오픈 연습은 그대로 할 수 있어요.</p></div>
    <div class="btns">${lastHand ? '<button class="ghost" id="bz-last" type="button">마지막 핸드 보기</button>' : ''}<button class="primary" id="bz-quiz" type="button">핸드 퀴즈 하러 가기</button></div>`;
  const l = $('bz-last'); if (l) l.onclick = () => openSheet(handEndHtml(lastHand.v, lastHand.n) + '<button class="ghost" id="x2" type="button">닫기</button>', b => b.querySelector('#x2').onclick = closeSheet);
  $('bz-quiz').onclick = () => ST.quiz();
  renderChips();
  if (t !== Infinity) { clearTimeout(showBust._t); showBust._t = setTimeout(async () => { if (await loadAcct() && A.s > 0) showTable(); }, Math.min(Math.max(1000, t - Date.now() + 1500), 6 * 36e5)); }
}
function showTable() {
  $('gate').hidden = true; $('main').hidden = false;
  renderChips();
  const heroSeat = heroPosFor(A.th);
  const demo = { heroPos: heroSeat, board: [], pot: 0, seats: POSITIONS.map(p => ({ pos: p, stack: p === heroSeat ? A.s : cfg().start, inv: 0, folded: false, hero: p === heroSeat, lastAct: '', cards: p === heroSeat ? [null, null] : null, inHand: false })), log: [] };
  prepHand(); renderTable(demo);
  $('b-start').hidden = false; $('b-start').textContent = A.h ? `이어서 치기 · 내 스택 ${fmt(A.s)}BB` : `게임 시작 · ${fmt(A.s)}BB`;
  $('status').textContent = ''; wait('');
}

// ---------- 설정: 빌런 8명 성향 ----------
function styleSel(v, id) { return `<select id="${id}" aria-label="성향">${STYLE_KEYS.map(k => `<option value="${k}"${k === v ? ' selected' : ''}>${VILLAIN_STYLES[k].name}</option>`).join('')}</select>`; }
function openSettings() {
  const c = cfg(), s8 = styles8(), hp = heroPosFor(A ? A.th : 0);
  openSheet(`<div class="sheethead"><h2>테이블 설정</h2><button class="closebtn" id="s-x" type="button">닫기</button></div>
    <div class="startbox"><span>시작 스택</span><b>${c.start}BB</b></div>
    <p class="meta" style="font-size:13px;line-height:1.6">힌트 없이 치고, 빌런은 솔버 전략을 바탕으로 둬요. 스택을 다 잃으면 이번 판은 끝나요. 빌런 1은 내 왼쪽 자리이고, 버튼이 돌면 자리 이름도 같이 바뀌어요.</p>
    <div class="allset"><span>빌런 8명 성향</span><select id="s-all" aria-label="한 번에 바꾸기"><option value="" selected>한 번에 바꾸기</option>${STYLE_KEYS.map(k => `<option value="${k}">${VILLAIN_STYLES[k].name}</option>`).join('')}</select></div>
    <div class="vlist">${s8.map((v, i) => `<div class="vrow"><b>빌런 ${i + 1}</b><small>다음 핸드 ${POS_KO[villainPos(hp, i + 1)]}</small>${styleSel(v, 's-v' + i)}</div>`).join('')}</div>
    <div class="legend">${STYLE_KEYS.map(k => `<span><span class="dot" style="background:${STYLE_DOT[k]}"></span>${VILLAIN_STYLES[k].name}</span>`).join('')}</div>
    <p class="meta">성향은 빌런이 실제로 고르는 액션만 바꿔요. 채점과 EV는 항상 GTO 기준이에요. 바꾼 성향은 다음 핸드부터 적용돼요.</p>
    <button class="primary" id="s-save" type="button">저장하고 닫기</button>`, b => {
    b.querySelector('#s-x').onclick = closeSheet;
    b.querySelector('#s-all').onchange = e => { const v = e.target.value; if (!v) return; for (let i = 0; i < 8; i++) b.querySelector('#s-v' + i).value = v; };
    b.querySelector('#s-save').onclick = () => {
      if (A) { A.st = Array.from({ length: 8 }, (_, i) => b.querySelector('#s-v' + i).value); saveNow(); }
      closeSheet(); toast('저장했어요. 다음 핸드부터 적용돼요.');
    };
  });
}
$('b-set').onclick = () => { if (A) openSettings(); };

// ---------- 통계 ----------
function statsHtml() {
  const s = game ? game.stats : (savedStats || { hands: 0, net: 0, evLoss: 0, decisions: 0, postDecisions: 0, good: 0, preDecisions: 0, preMistakes: 0, preLoss: 0, history: [] });
  const per100 = x => s.hands ? sgn(x / s.hands * 100) : '–';
  const H = s.history || [];
  let chart = '<p class="meta">핸드를 치면 그래프가 생겨요.</p>';
  if (H.length > 1) {
    const W = 600, Ht = 200, pad = 34;
    const ys1 = H.map(h => h.net), ys2 = H.map(h => -h.evLoss);
    const minY = Math.min(0, ...ys1, ...ys2), maxY = Math.max(0, ...ys1, ...ys2), span = (maxY - minY) || 1;
    const X = i => pad + (i / (H.length - 1)) * (W - pad - 10), Y = v => 10 + (1 - (v - minY) / span) * (Ht - 30);
    const line = ys => ys.map((v, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join('');
    chart = `<svg viewBox="0 0 ${W} ${Ht}" role="img" aria-label="누적 손익과 누적 EV 손실">
      <line x1="${pad}" x2="${W - 10}" y1="${Y(0)}" y2="${Y(0)}" stroke="#2A2F3B"/><text x="${pad - 6}" y="${Y(0) + 4}" text-anchor="end" font-size="11" fill="#A39C8E" font-family="monospace">0</text>
      <path d="${line(ys1)}" fill="none" stroke="#7FD4A0" stroke-width="2.5"/><path d="${line(ys2)}" fill="none" stroke="#D4AF7C" stroke-width="2" stroke-dasharray="5 4"/>
      <text x="${W - 10}" y="${Ht - 4}" text-anchor="end" font-size="11" fill="#A39C8E" font-family="monospace">${H[H.length - 1].n}핸드</text></svg>
      <div class="legend"><span style="color:#7FD4A0">━ 누적 손익(BB)</span><span style="color:#D4AF7C">┅ 누적 EV 손실(−BB)</span></div>`;
  }
  const recent = H.slice(-10).reverse().map(h => `<div class="opt" style="grid-template-columns:42px minmax(0,1fr) 60px 60px"><span class="r meta">#${h.n}</span><span class="nm">${POS_KO[h.heroPos]} · ${h.cards.map(cardTxt).join('')}${h.board && h.board.length ? ' · ' + h.board.map(cardTxt).join('') : ''}</span><span class="r" style="color:${h.handNet >= 0 ? 'var(--good)' : 'var(--bad)'}">${sgn(h.handNet)}</span><span class="r">−${fmt(h.handLoss, 2)}</span></div>`).join('');
  return `<div class="sheethead"><div><h2>통계</h2><span class="meta">이번 판은 내 계정 기록, 그래프·최근 핸드는 이 기기 기록</span></div><button class="closebtn" id="x" type="button">닫기</button></div>
    <div class="statgrid">
      <div class="tile hl"><span>내 스택</span><b>${A ? fmt(A.s) : '–'}</b></div><div class="tile"><span>이번 판 핸드</span><b>${A ? A.h : 0}</b></div><div class="tile"><span>최고 스택</span><b>${A ? fmt(A.best) : '–'}</b></div>
      <div class="tile hl"><span>EV 손실 합</span><b>${A ? fmt(A.ev, 1) : '–'}</b></div><div class="tile hl"><span>EV 손실 /100핸드</span><b>${A && A.h ? fmt(A.ev / A.h * 100, 1) : '–'}</b></div><div class="tile"><span>GTO 일치율</span><b>${A && A.dn ? pct(A.good / A.dn) : '–'}</b></div>
      <div class="tile"><span>이 기기 핸드</span><b>${s.hands}</b></div><div class="tile"><span>손익 /100핸드</span><b>${per100(s.net)}</b></div><div class="tile"><span>프리플랍 실수</span><b>${s.preMistakes}/${s.preDecisions}</b></div></div>
    <div class="dec"><b>추이</b><div class="chart">${chart}</div></div>
    ${recent ? `<div class="dec"><b>최근 핸드</b><div class="opt hdr" style="grid-template-columns:42px minmax(0,1fr) 60px 60px"><span></span><span>핸드</span><span class="r">손익</span><span class="r">EV 손실</span></div>${recent}</div>` : ''}
    <p class="meta">손익은 카드 운이 섞여 있어요. 실력은 EV 손실(GTO 최선 액션 대비 잃은 기대값)로 봐요.</p>`;
}
$('b-stats').onclick = () => openSheet(statsHtml(), b => { b.querySelector('#x').onclick = closeSheet; });

// ---------- 시작 ----------
(async function init() {
  const g = $('gate');
  const gate = (h, p, btn, fn) => { $('main').hidden = true; g.hidden = false; g.className = 'gate'; g.innerHTML = `<h2>${h}</h2><p>${p}</p>${btn ? `<button class="primary" id="g-go" type="button">${btn}</button>` : ''}`; if (btn) $('g-go').onclick = fn; };
  gate('불러오는 중…', '내 스택을 확인하고 있어요.');
  let w = ST.who();
  for (let i = 0; i < 40 && !w.ok && w.wait; i++) { await io.wait(250); w = ST.who(); }
  if (!w.ok) { gate('참가하면 칠 수 있어요', '접속 코드와 닉네임으로 참가하면 내 계정에 스택이 저장돼요. 폰·PC 어디서 열어도 같은 스택으로 이어서 쳐요.', '참가하기', () => ST.join()); return; }
  if (!(await loadAcct())) { gate('스택을 불러오지 못했어요', '인터넷 연결을 확인하고 다시 열어 주세요.', '다시 시도', () => location.reload()); return; }
  if (A.s <= 0) showBust(); else showTable();
})();
