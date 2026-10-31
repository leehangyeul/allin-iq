# 새 핸드 200개 + 다중 스택 오픈 연습(8·10·12·15·20BB 계산값)을 원본 HTML에 넣어요
import sys, json, re, os
HERE = os.path.dirname(os.path.abspath(__file__))
src_path = sys.argv[1]
S = open(src_path, encoding="utf-8").read()


def rep(old, new, cnt=1):
    global S
    n = S.count(old)
    assert n == cnt, (n, old[:80])
    S = S.replace(old, new)


# ---------- 1) 핸드 200개 ----------
SIT = {"pf_push": "f", "pf_call": "f", "pf_hu_push": "f", "pf_hu_call": "f", "pf10_push": "f", "pf10_call": "f",
       "short_rfi": "o", "rfi": "o", "rfi_mid": "o", "short_def": "b", "def": "b", "def_mid": "b",
       "short_ipdef": "p", "ipdef": "p", "ipdef_mid": "p", "vs3b": "t", "mw": "m"}
hands = json.load(open(os.path.join(HERE, "new200.json")))
clean = [{k: v for k, v in h.items() if not k.startswith("_")} for h in hands]
if "const NEW200=" not in S:
    i = S.index("NEW150.forEach(h=>LEVELS[0].hands.push(h));")
    j = i + len("NEW150.forEach(h=>LEVELS[0].hands.push(h));")
    S = S[:j] + "\n// 2026-11 추가 200개: 푸시/폴드는 자체 계산(cv:1), 나머지는 예시 빈도(GTO 감각 테스트)\nconst NEW200=" + json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + ";\nNEW200.forEach(h=>LEVELS[0].hands.push(h));" + S[j:]
    # 상황 태그와 헤즈업 EV 태그
    m = re.search(r"const HSIT=(\{.*?\});", S)
    d = json.loads(m.group(1))
    for h in hands: d[h["me"] + "|" + "".join(h["hand"])] = SIT[h["_kind"]]
    S = S[:m.start(1)] + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + S[m.end(1):]
    m = re.search(r"const HEV=(\[.*?\]);", S)
    e = json.loads(m.group(1))
    for h in hands:
        if h["_kind"] in ("pf_hu_push", "pf_hu_call"): e.append(h["me"] + "|" + "".join(h["hand"]))
    S = S[:m.start(1)] + json.dumps(e, ensure_ascii=False, separators=(",", ":")) + S[m.end(1):]

# ---------- 2) 오픈 연습 데이터: 5개 스택을 압축 문자열로 ----------
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
encF = lambda a: "".join(B64[max(0, min(63, round(x * 63)))] for x in a)
def encE(a):
    o = []
    for x in a:
        v = max(0, min(4095, round(x * 100) + 2048)); o.append(B64[v // 64] + B64[v % 64])
    return "".join(o)
m = re.search(r"const DRILL_PF10=(\{.*?\});\n", S)
if m:
    P = {"10": json.loads(m.group(1))}
    for s in (8, 12, 15, 20): P[str(s)] = json.load(open(os.path.join(HERE, "..", "pf2", f"pf_{s}.json")))
    Z = {}
    for st in ("8", "10", "12", "15", "20"):
        T = P[st]
        Z[st] = {"j": {k: encF(v) for k, v in T["jam"].items()}, "je": {k: encE(v) for k, v in T["jam_ev"].items()},
                 "c": {k: encF(v) for k, v in T["call"].items()}, "ce": {k: encE(v) for k, v in T["call_ev"].items()}}
    dec = ("const DRILL_PFZ=" + json.dumps(Z, separators=(",", ":")) + ";\n"
           "const PFST=[8,10,12,15,20],PFB64=\"" + B64 + "\";\n"
           "const DRILL_PF=(()=>{const F=s=>[...s].map(c=>PFB64.indexOf(c)/63),E=s=>{const o=[];for(let i=0;i<s.length;i+=2)o.push((PFB64.indexOf(s[i])*64+PFB64.indexOf(s[i+1])-2048)/100);return o};\n"
           "  const o={};for(const st in DRILL_PFZ){const z=DRILL_PFZ[st],m=f=>Object.fromEntries(Object.entries(z[f]).map(([k,v])=>[k,f.length>1?E(v):F(v)]));o[st]={jam:m(\"j\"),jam_ev:m(\"je\"),call:m(\"c\"),call_ev:m(\"ce\")}}return o})();\n"
           "const pfNear=D=>PFST.reduce((a,b)=>Math.abs(b-D)<Math.abs(a-D)?b:a,PFST[0]);\n")
    S = S[:m.start()] + dec + S[m.end():]

# ---------- 3) 오픈 연습 코드 ----------
rep("""// 15·25·40·75BB: 프리플랍 강의 교재 차트(학습용 분류, 혼합 빈도 아님) → "차트와 일치" 연습으로만 채점.
// 10BB: 앱과 같은 조건으로 직접 계산한 푸시/폴드 근사(첫 콜러 모델) → 빈도와 EV로 채점.""",
"""// 오픈 연습은 8·10·12·15·20BB 올인/폴드와 올인 대응만 써요. 9인 BB 앤티, 첫 콜러 모델, 칩 EV로 직접 계산한 근사 → 빈도와 EV로 채점.
// (교재 차트 DRILL_CHARTS는 핸드 퀴즈 해설의 깊은 스택 참고용으로만 남아 있어요.)""")
rep("""function dSpot(){
  const u=Math.random();
  if(u<0.50){const c=dPick(DRILL_CHARTS.filter(c=>c.spot==="rfi"&&c.pos!=="SB"));return{kind:"chart",...c}}
  if(u<0.62){const c=dPick(DRILL_CHARTS.filter(c=>c.spot==="rfi"&&c.pos==="SB"));return{kind:"chart",...c}}
  if(u<0.70){const c=DRILL_CHARTS.find(c=>c.spot==="vs_open");return{kind:"chart",...c}}
  if(u<0.88){const p=dPick(DPOS.slice(0,8));return{kind:"pf10",st:10,pos:p,spot:"rfi"}}
  const k=dPick(Object.keys(DRILL_PF10.call));const [op,pos]=k.split(">");return{kind:"pf10",st:10,pos,op,spot:"vs_shove"}
}""", """function dSpot(){
  const st=dPick(PFST),P=DRILL_PF[st];
  if(Math.random()<0.5){const p=dPick(DPOS.slice(0,8));return{kind:"pf",st,pos:p,spot:"rfi"}}
  const k=dPick(Object.keys(P.call));const [op,pos]=k.split(">");return{kind:"pf",st,pos,op,spot:"vs_shove"}
}
const pfF=sp=>sp.spot==="rfi"?DRILL_PF[sp.st].jam[sp.pos]:DRILL_PF[sp.st].call[sp.op+">"+sp.pos];
const pfE=sp=>sp.spot==="rfi"?DRILL_PF[sp.st].jam_ev[sp.pos]:DRILL_PF[sp.st].call_ev[sp.op+">"+sp.pos];""")
rep("""// spots: chart RFI (7 positions x 4 stacks), SB first-in (4), BB vs BTN 40BB, 10BB jam (8), 10BB facing a jam (36)""",
    """// spots: 5 stacks (8·10·12·15·20BB) x (first-in jam 8 + facing a jam 36) = 220""")
rep("""  const f=sp.spot==="rfi"?DRILL_PF10.jam[sp.pos]:DRILL_PF10.call[sp.op+">"+sp.pos];
  return f.map(""", """  const f=pfF(sp);
  return f.map(""")
rep("""  const isR=sp.spot==="rfi",k=sp.op+">"+sp.pos;const f=isR?DRILL_PF10.jam[sp.pos][idx]:DRILL_PF10.call[k][idx];const ev=Math.abs(isR?DRILL_PF10.jam_ev[sp.pos][idx]:DRILL_PF10.call_ev[k][idx]);""",
    """  const f=pfF(sp)[idx];const ev=Math.abs(pfE(sp)[idx]);""")
rep("""  if(sp.kind==="pf10")return sp.spot==="rfi"?["f","j"]:["f","c"];""", """  if(sp.kind==="pf")return sp.spot==="rfi"?["f","j"]:["f","c"];""")
rep("""act:sp.spot==="vs_shove"?"올인":"오픈",bet:sp.spot==="vs_shove"?10:2.2,""", """act:sp.spot==="vs_shove"?"올인":"오픈",bet:sp.spot==="vs_shove"?stack:2.2,""")
rep("""  if(opener){pot+=sp.spot==="vs_shove"?10:2.2}""", """  if(opener){pot+=sp.spot==="vs_shove"?stack:2.2}""")
rep("""  return `${sp.op} 올인 10BB → 사이 자리 모두 폴드 → 히어로 차례`;""", """  return `${sp.op} 올인 ${sp.st}BB → 사이 자리 모두 폴드 → 히어로 차례`;""")
rep("""function dSource(sp){return sp.kind==="chart"?`프리플랍 차트 · ${sp.st}BB`:"10BB 직접 계산 근사 · 첫 콜러 모델 · cEV"}""",
    """function dSource(sp){return sp.kind==="chart"?`프리플랍 차트 · ${sp.st}BB`:`${sp.st}BB 직접 계산 근사 · 9인 BB 앤티 · 첫 콜러 모델 · cEV`}""")
rep("""${sp.kind==="chart"?"차트 분류와 같은지 확인하는 연습이에요. GTO 빈도 점수가 아니에요.":"10BB 계산 근사의 빈도와 EV로 채점해요."}""",
    """${sp.kind==="chart"?"차트 분류와 같은지 확인하는 연습이에요. GTO 빈도 점수가 아니에요.":`${sp.st}BB 계산 근사의 빈도와 EV로 채점해요.`}""")
rep("""  if(sp.kind==="pf10")freq=sp.spot==="rfi"?DRILL_PF10.jam[sp.pos]:DRILL_PF10.call[sp.op+">"+sp.pos];""", """  if(sp.kind==="pf")freq=pfF(sp);""")
rep("""`${sp.op}의 10BB 올인에 ${sp.pos}가 콜하는 비율은 ${play.toFixed(1)}%`""", """`${sp.op}의 ${sp.st}BB 올인에 ${sp.pos}가 콜하는 비율은 ${play.toFixed(1)}%`""")
rep("""  else{const isR=sp.spot==="rfi",k=sp.op+">"+sp.pos;const f=isR?DRILL_PF10.jam[sp.pos][idx]:DRILL_PF10.call[k][idx];const ev=isR?DRILL_PF10.jam_ev[sp.pos][idx]:DRILL_PF10.call_ev[k][idx];""",
    """  else{const isR=sp.spot==="rfi";const f=pfF(sp)[idx];const ev=pfE(sp)[idx];""")
rep("""계산 근사 ${dActLabel(sp,go)} ${(f*100).toFixed(1)}% · 폴드 ${((1-f)*100).toFixed(1)}%""", """계산 근사 ${dActLabel(sp,go)} ${Math.round(f*100)}% · 폴드 ${Math.round((1-f)*100)}%""")

# ---------- 4) 핸드 퀴즈 해설의 차트 참고 ----------
rep("""    if(D===10)return{sp:{kind:"pf10",st:10,pos:me,spot:"rfi"},exact:true};""",
    """    if(D<=12||h.cv){const st=pfNear(D);return{sp:{kind:"pf",st,pos:me,spot:"rfi"},exact:st===D,from:st}}""")
old = re.search(r'  if\(!h\.multi&&/올인/\.test\(h\.s\[0\]\.a\)&&D<=15&&DPOS\.indexOf\(QPOS\(h\.vs\)\)<DPOS\.indexOf\(me\)\)\{[^\n]*\n', S).group(0)
rep(old, """  if(!h.multi&&/올인/.test(h.s[0].a)&&(D<=15||h.cv)&&DPOS.indexOf(QPOS(h.vs))<DPOS.indexOf(me)){const st=pfNear(D),k=QPOS(h.vs)+">"+me;if(DRILL_PF[st].call[k])return{sp:{kind:"pf",st,pos:me,op:QPOS(h.vs),spot:"vs_shove"},exact:st===D,from:st}}\n""")
rep("""  else{const f=sp.spot==="rfi"?DRILL_PF10.jam[sp.pos][idx]:DRILL_PF10.call[sp.op+">"+sp.pos][idx];verdict=`10BB 계산 근사에서""",
    """  else{const f=pfF(sp)[idx];verdict=`${sp.st}BB 계산 근사에서""")
rep("""자료에 있는 건 첫 진입, SB 첫 진입, 40BB BB vs BTN 오픈 대응, 10BB 올인·콜 계산뿐이에요.""", """자료에 있는 건 첫 진입, SB 첫 진입, 40BB BB vs BTN 오픈 대응, 8~20BB 올인·콜 계산뿐이에요.""")
rep("""  const D=h.d||100,S=rgBucket(D),d=decs[0];if(!S||!d)return{sum:[],html:chartBlock(h)};const sum=[];""",
    """  const D=h.d||100,S=rgBucket(D),d=decs[0];
  if(h.cv&&d){const ref=chartRef(h);if(ref){const sp=ref.sp,i=clsIdx(h.hand),f=pfF(sp)[i],ev=pfE(sp)[i],go=sp.spot==="rfi"?"올인":"콜";
    return{sum:[["계산",`<b>${DH[i]} → ${go} ${Math.round(f*100)}%</b><em>${sp.st}BB 계산 근사 · ${go} EV ${ev>=0?"+":""}${ev.toFixed(2)}BB · 히어로 선택 ${lab(d.o,d.k)}</em>`]],html:chartBlock(h)}}}
  if(!S||!d)return{sum:[],html:chartBlock(h)};const sum=[];""")
rep("""function pfChartLetter(h){
  try{""", """function pfChartLetter(h){
  if(h.cv)return null; // 자체 계산 푸시/폴드 문제는 교재 차트로 바꾸지 않아요
  try{""")

# ---------- 5) 코치 문구 ----------
rep("""오픈 연습에서 앞 포지션만 20문제를 풀어 보세요. 경계 핸드(A9o, KTo, 작은 수티드 커넥터)가 자주 나와요.""", """오픈 연습에서 앞 포지션만 20문제를 풀어 보세요. 올인 범위가 좁아서 경계 핸드(A9o, KTo, 작은 페어)가 자주 나와요.""")
rep("""오픈 연습에서 CO와 BTN만 20문제를 풀어 보세요. 약한 에이스와 수티드 커넥터가 자주 나와요.""", """오픈 연습에서 CO와 BTN만 20문제를 풀어 보세요. 약한 에이스와 수티드 킹이 경계에 자주 나와요.""")
rep("""SB에서는 림프와 레이즈 중 어느 쪽이 스택에 맞는지 확인해 보세요.""", """SB에서는 BB 한 명만 남았을 때 올인 범위가 얼마나 넓어지는지 확인해 보세요.""")
rep("""오픈 연습에서 40BB 이상 차트만 골라 풀어 보세요.""", """핸드 퀴즈에서 40BB 이상 판이 나오면 첫 결정을 한 번 더 천천히 확인해 보세요.""")
rep("""오픈 연습에서 25BB 차트만 골라 풀어 보세요.""", """오픈 연습의 20BB 문제로 올인 범위가 어디까지 넓어지는지 확인해 보세요.""")
rep("""오픈 연습에서 10~15BB 문제만 20개 풀어 보세요.""", """오픈 연습에서 8~15BB 문제만 20개 풀어 보세요.""")
rep("""  if(id==="stk:deep")return `<button class="cta cof" data-cf="${id}">깊은 스택만 오픈 연습하기</button>`;""",
    """  if(id==="stk:deep")return `<button class="cta cof" data-cf="${id}">핸드 퀴즈 하러 가기</button>`;""")
rep("""  if(id==="stk:deep")return drillStart({st:[40,100]});""", """  if(id==="stk:deep")return start(0);""")

# ---------- 6) 관리자 난이도 설명 ----------
rep("""      <li><b>오픈 연습 · 차트</b>같은 킥커 줄(예: K9s·K8s·K7s…)에서 바로 옆 핸드와 행동이 다르면 어려움, 두 칸 옆에서 바뀌면 보통, 그 외는 쉬움</li>
      <li><b>오픈 연습 · 10BB</b>올인/콜과 폴드를 섞어 쓰거나 EV 차이가 0.3BB 미만이면 어려움, 1BB 미만이면 보통, 그 이상이면 쉬움</li>""",
    """      <li><b>오픈 연습 · 8~20BB</b>올인/콜과 폴드를 섞어 쓰거나 EV 차이가 0.3BB 미만이면 어려움, 1BB 미만이면 보통, 그 이상이면 쉬움</li>""")

assert "DRILL_PF10" not in S, [m.start() for m in re.finditer("DRILL_PF10", S)]
assert '"pf10"' not in S
open(src_path, "w", encoding="utf-8").write(S)
print("ok", len(S))
