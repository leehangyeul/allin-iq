# 통합 GTO 차트(merged.json)를 GTO 홀덤 테이블(솔버 게임)의 프리플랍 차트 기본값으로 넣어요. 2026-11-03
# 사용: python3 apply_solver.py <솔버.html> <결과.html>
# - 15·25·40·75(=100-75)bb 구간의 RFI·SB 퍼스트 인·오픈 대응·BB vs SB 레이즈 칸을 통합 차트로 덮어써요.
#   한 액션 칸 = 그 액션 100%, 믹스 칸 = 두 액션 50%씩(폴드는 칠하지 않음).
# - 10bb(푸시·폴드), BB vs SB 림프, SB 림프 후 대응, 3벳 대응(오프너)은 솔버 계산 그대로 두되, 덮어쓴 레인지를 바탕으로 다시 만들어져요.
import json,sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src,encoding="utf-8").read()
M=json.load(open("merged.json"))
U={S:{k:[v["g"],v["x"]] for k,v in M[S].items()} for S in M}
def rep(old,new,cnt=1):
    global s
    n=s.count(old);assert n==cnt,(n,old[:80]);s=s.replace(old,new)

js='''// ---------- 통합 GTO 차트 (2026-11-03) ----------
// 솔버 차트와 기준 차트를 칸마다 비교해 공통 분모는 그 액션, 갈리는 칸은 믹스(두 액션 반반)로 합친 차트.
// 75 구간 = 100-75bb 공통. 글자: r 오픈·레이즈·3벳 · j 올인 · l 림프 · c 콜 · f 폴드. [g, x] (x '.'=한 액션)
const UNIFIED = '''+json.dumps(U,separators=(",",":"))+''';
function unifiedLayer(cell, L) { const [g, x] = cell; const w = new Float32Array(169);
  for (let k = 0; k < 169; k++) w[k] = x[k] === '.' ? (g[k] === L ? 1 : 0) : (g[k] === L ? 0.5 : 0) + (x[k] === L ? 0.5 : 0); return w; }
function applyUnifiedOpen(C, bucket) { const U = UNIFIED[bucket]; if (!U) return;
  const nm = { UTG: 'UTG', UTG1: 'UTG+1', UTG2: 'UTG+2', LJ: 'LJ', HJ: 'HJ', CO: 'CO', BTN: 'BTN' };
  for (const p of POS) { const c = U['O:' + nm[p]]; if (!c) continue; C[`rfi.${p}.raise`] = unifiedLayer(c, 'r'); C[`rfi.${p}.jam`] = unifiedLayer(c, 'j'); }
  const sb = U['O:SB']; if (sb) { C['sb.raise'] = unifiedLayer(sb, 'r'); C['sb.jam'] = unifiedLayer(sb, 'j'); C['sb.limp'] = unifiedLayer(sb, 'l'); } }
function applyUnifiedDef(C, bucket) { const U = UNIFIED[bucket]; if (!U) return;
  const og = { EP: 'UTG', MP: 'LJ/HJ', CO: 'CO', BTN: 'BTN' };
  const dn = (g, d) => d === 'UTG1' || d === 'UTG2' ? 'UTG+1/+2' : (g === 'EP' && (d === 'LJ' || d === 'HJ')) ? 'LJ/HJ' : d;
  for (const g of ['EP', 'MP', 'CO', 'BTN']) for (const d of Object.keys(T.def[bucket][g])) {
    const c = U[`D:${dn(g, d)}<${og[g]}`] || (g === 'MP' ? U[`D:${d}<LJ`] : null); if (!c) continue;
    C[`def.${g}.${d}.threebet`] = unifiedLayer(c, 'r'); C[`def.${g}.${d}.jam`] = unifiedLayer(c, 'j'); C[`def.${g}.${d}.call`] = unifiedLayer(c, 'c'); }
  const b = U['D:BB<SB']; if (b) { C['bbr.threebet'] = unifiedLayer(b, 'r'); C['bbr.jam'] = unifiedLayer(b, 'j'); C['bbr.call'] = unifiedLayer(b, 'c'); } }

// ---------- 차트 생성 ----------'''
rep("// ---------- 차트 생성 ----------",js)
# SB 퍼스트 인 직후(림프 관련 차트가 통합 차트의 림프 레인지를 쓰도록) / 오픈 대응 직후
rep("    C['sb.raise'] = raise; C['sb.jam'] = jam; C['sb.limp'] = limp;\n  }\n","    C['sb.raise'] = raise; C['sb.jam'] = jam; C['sb.limp'] = limp;\n  }\n  applyUnifiedOpen(C, bucket); // 통합 GTO 차트(15·25·40·100-75bb)\n")
rep("  // 3벳(올인 아님) 대응: 오프너\n","  applyUnifiedDef(C, bucket); // 통합 GTO 차트\n  // 3벳(올인 아님) 대응: 오프너\n")
# 화면 문구
rep("${bucket === 10 ? '푸시·폴드(12bb 이하)' : bucket + 'bb'}</b> 구간 차트를 고쳐요. 기본값은 자료(Little 프리플랍 마스터클래스)의 포지션별 빈도에 맞춘 근사치예요.</p>",
    "${bucket === 10 ? '푸시·폴드(12bb 이하)' : bucket === 75 ? '100-75bb' : bucket + 'bb'}</b> 구간 차트를 고쳐요. 기본값은 통합 GTO 차트예요(솔버 차트와 기준 차트의 공통 분모, 갈리는 칸은 믹스 50%).</p>")
rep("프리플랍은 스택 구간별 차트(자료 기준 근사)와 올인 EV 계산으로","프리플랍은 스택 구간별 통합 GTO 차트(15·25·40·100-75bb)와 올인 EV 계산으로")
open(dst,"w",encoding="utf-8").write(s);print("저장",dst,len(s))
