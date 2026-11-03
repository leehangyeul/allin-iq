# 합친 프리플랍 차트(merged.json)를 웹앱 원본에 넣어요. 2026-11-02
# 사용: python3 apply_merged.py <원본.html> <결과.html>
import json,re,sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src,encoding="utf-8").read()
M=json.load(open("merged.json"))
def rep(old,new,cnt=1):
    global s
    n=s.count(old)
    assert n==cnt,(n,old[:90])
    s=s.replace(old,new)
def rerep(pat,new,cnt=1):
    global s
    s2,n=re.subn(pat,lambda m:new,s,flags=re.S)
    assert n==cnt,(n,pat[:90]);s=s2

# 1. 차트 데이터 교체 (페이지 번호 없음)
rerep(r'// 교재 차트 레인지 라이브러리[^\n]*\nconst RANGES=\{.*?\};',
      '// 프리플랍 차트 (15·25·40·75BB, 첫 진입·오픈 대응): 통합 GTO 차트. 솔버(GTO 홀덤 테이블) 차트와 기준 차트를 칸마다 비교해 공통 분모는 그 액션, 갈리는 칸은 믹스. 75 = 100-75BB 공통.\n'
      '// 두 쪽이 같은 칸은 한 행동, 갈리는 칸은 섞음. g=믹스일 때 왼쪽(공격적인) 액션, x=오른쪽 액션("."이면 한 행동). 글자: r 오픈/3벳 · j 올인 · c 콜 · l 림프 · f 폴드\n'
      'const RANGES='+json.dumps(M,separators=(",",":"))+';')
rerep(r'const DRILL_CHARTS=\[.*?\];\n','')
rep('// (교재 차트 DRILL_CHARTS는 핸드 퀴즈 해설의 깊은 스택 참고용으로만 남아 있어요.)\n','')
rep('// 레인지 출처: 프리플랍 강의 교재 차트(학습용 분류)를 범위 그대로 사용해요. 빈도로 바꾸지 않아요.',
    '// 레인지 출처: 위 프리플랍 차트. 섞음 칸은 절반 비중으로 넣어요.')
rep('// ================= 핸드 퀴즈 상세 해설: 실제 계산 + 교재 차트 =================',
    '// ================= 핸드 퀴즈 상세 해설: 실제 계산 + 프리플랍 차트 =================')

# 2. 첫 결정의 차트 칸 + 정답 맞추기
i=s.index('// ---- 프리플랍 첫 결정의 정답을 교재 차트 분류와 맞춤 ----');j=s.index('\n// 해설 문장을 정답',i)
s=s[:i]+r'''// ---- 프리플랍 첫 결정의 정답을 프리플랍 차트에 맞춤 ----
// 한 행동 칸: 그 행동이 가장 높은 빈도가 되게 기존 빈도 자리를 바꿔요. 섞음 칸: 두 행동이 1·2위가 되고 비율을 53:47로 비슷하게 맞춰요.
// 첫 진입(O:)과 오픈 1:1 대응(D:)만 써요. 3벳·4벳·올인을 받은 결정은 차트가 없어 그대로 둬요.
function chartCell(h){
  try{if(h.cv||isHU(h))return null;const D=h.d||100,S=rgBucket(D);if(!S)return null;const s0=h.s&&h.s[0];if(!s0)return null;
    const me=QPOS(h.me),v1=QPOS(h.vs),a=s0.a,unopened=h.pf[1]<=1;
    if(/히어로 [\d.]+BB 오픈 → 빌런 3벳/.test(a)||/빌런 4벳/.test(a)||/빌런 [\d.]+BB 올인/.test(a))return null;
    let key,spot;if(unopened){if(me==="BB")return null;key="O:"+me;spot="rfi"}else{key=defKey(me,v1);spot="vs_open"}
    const c=key&&(RANGES[S]||{})[key];if(!c)return null;const i=clsIdx(h.hand);
    return{S,key,spot,op:v1,g:c.g,x:c.x,a:c.g[i],b:c.x[i]==="."?null:c.x[i]}}catch(e){return null}
}
// strict: 섞음의 둘째 행동은 같은 종류의 선택지만 (작은 3벳을 올인으로 대신하지 않아요)
function chartOptKey(keys,L,strict){const isR=k=>k==="raise"||/^b\d+$/.test(k);
  return L==="f"?keys.find(k=>k==="fold"):L==="j"?keys.find(k=>k==="jam"):(L==="c"||L==="l")?keys.find(k=>k==="call"):(keys.find(isR)||(strict?undefined:keys.find(k=>k==="jam")))}
function chartAlign(){let n=0;
  LEVELS.forEach(L=>L.hands.forEach(h=>{const s0=h.s&&h.s[0];if(!s0||h.__al)return;h.__al=1;
    const c=chartCell(h);if(!c)return;
    const keys=s0.o.map(x=>x[0]);let ta=chartOptKey(keys,c.a,c.spot==="vs_open"),tb=c.b?chartOptKey(keys,c.b,true):null;
    if(!ta){ta=tb;tb=null}if(!ta)return;if(tb===ta)tb=null;
    const f=s0.f,before=JSON.stringify(f);
    const sw=(k,rank)=>{const order=keys.slice().sort((x,y)=>(+f[y]||0)-(+f[x]||0));const o=order[rank];if(o&&o!==k){const t=f[k]||0;f[k]=f[o]||0;f[o]=t}};
    sw(ta,0);
    if(!tb){ // 한 행동 칸은 그 행동이 확실히 1위(65% 이상): 모자라면 2위에서 가져와요
      const sec=keys.filter(k=>k!==ta).sort((x,y)=>(+f[y]||0)-(+f[x]||0))[0];
      if(sec&&(+f[ta]||0)<65){const d=Math.min(+f[sec]||0,65-(+f[ta]||0));f[ta]=(+f[ta]||0)+d;f[sec]=(+f[sec]||0)-d}}
    if(tb){const rest=keys.filter(k=>k!==ta).sort((x,y)=>(+f[y]||0)-(+f[x]||0));const o=rest[0];if(o&&o!==tb){const t=f[tb]||0;f[tb]=f[o]||0;f[o]=t}
      const sum=(+f[ta]||0)+(+f[tb]||0);f[ta]=Math.round(sum*0.53);f[tb]=Math.round(sum-f[ta])}
    if(JSON.stringify(f)!==before)n++}));
  return n}
'''+s[j:]

# 3. 해설 차트 연결
i=s.index('function chartRef(h){');j=s.index('\nfunction chartBlock(h){',i)
s=s[:i]+r'''function chartRef(h){
  const D=h.d||100,me=QPOS(h.me),pf=h.pf;const unopened=pf[1]<=1;
  if(isHU(h))return h.me==="SB"?{sp:{kind:"hu",st:D,pos:"SB",spot:"rfi"},exact:true,from:D}:{sp:{kind:"hu",st:D,pos:"BB",op:"SB",spot:"vs_shove"},exact:true,from:D};
  if(unopened&&me!=="BB"&&(D<=12||h.cv)){const st=pfNear(D);return{sp:{kind:"pf",st,pos:me,spot:"rfi"},exact:st===D,from:st}}
  if(!h.multi&&/올인/.test(h.s[0].a)&&(D<=15||h.cv)&&DPOS.indexOf(QPOS(h.vs))<DPOS.indexOf(me)){const st=pfNear(D),k=QPOS(h.vs)+">"+me;if(DRILL_PF[st].call[k])return{sp:{kind:"pf",st,pos:me,op:QPOS(h.vs),spot:"vs_shove"},exact:st===D,from:st}}
  const c=chartCell(h);
  if(c)return{sp:{kind:"chart",st:c.S,pos:me,op:c.op,spot:c.spot,g:c.g,x:c.x,multi:!!h.multi},exact:c.S===D||(c.S===75&&D>=75&&D<=100),from:c.S};
  return null;
}'''+s[j:]
# 원래 isHU 줄이 한 줄 return 형태였는지 확인용: 위에서 새로 작성

rep('''if(!ref)return `<div class="dx"><b>프리플랍 차트</b><p>이 프리플랍 상황(${h.multi?"멀티웨이 ":""}${h.vs} 액션 뒤 ${h.me})에 맞는 차트는 없어요. 자료에 있는 건 첫 진입, SB 첫 진입, 40BB BB vs BTN 오픈 대응, 8~20BB 올인·콜 계산뿐이에요.</p></div>`;''',
    '''if(!ref)return `<div class="dx"><b>프리플랍 차트</b><p>이 프리플랍 상황(${h.multi?"멀티웨이 ":""}${h.vs} 액션 뒤 ${h.me})에 맞는 차트는 없어요. 차트가 있는 건 첫 진입, 오픈에 대한 1:1 대응, 8~20BB 올인·콜 계산이에요.</p></div>`;''')
rep('''if(sp.kind==="chart")verdict=`차트에서 ${cls} 핸드는 <b>${dActLabel(sp,sp.g[idx])}</b>`;''',
    '''if(sp.kind==="chart")verdict=`차트에서 ${cls} 핸드는 <b>${dCellLabel(sp,idx)}</b>`+(sp.x[idx]!=="."?`. 직접 계산과 기준 차트가 갈리는 경계 핸드라 두 행동을 비슷하게 섞어요`:"")+(sp.multi?`. 앞에 콜러가 있어 1:1 대응 차트로 근사했어요`:"");''')
rep('''return `<div class="dx"><b>프리플랍 차트 · ${sp.st}BB ${sp.pos}${sp.spot==="vs_open"?" vs BTN 오픈":sp.spot==="vs_shove"?" vs "+sp.op+" 올인":" 첫 진입"}</b>''',
    '''return `<div class="dx"><b>프리플랍 차트 · ${sp.st}BB ${sp.pos}${sp.spot==="vs_open"?" vs "+sp.op+(sp.op==="SB"?" 레이즈":" 오픈"):sp.spot==="vs_shove"?" vs "+sp.op+" 올인":" 첫 진입"}</b>''')

# 4. 차트 그리기·설명
rep('''function dActLabel(sp,l){
  if(l==="r"){if(sp.spot==="vs_open")return"3벳";if(sp.pos==="SB")return"레이즈 3.5BB";return sp.st>=40?"오픈 2.2BB":"오픈 2BB"}
  return DACT[l];
}''','''function dActLabel(sp,l){
  if(l==="r"){if(sp.spot==="vs_open")return"3벳";if(sp.pos==="SB")return"레이즈";return sp.st>=40?"오픈 2.2BB":"오픈 2BB"}
  if(l==="j"&&sp.spot==="vs_open")return"올인(3벳)";
  return DACT[l];
}
// 섞음 칸이면 "오픈·폴드 섞음"
function dCellLabel(sp,i){const x=sp.x&&sp.x[i]!=="."?sp.x[i]:null;return x?`${dActLabel(sp,sp.g[i])}·${dActLabel(sp,x)} 섞음`:dActLabel(sp,sp.g[i])}''')
rep('''  const cells=DH.map((h,i)=>{const bg=freq?`linear-gradient(90deg,${DCOL[sp.spot==="rfi"?"j":"c"]} ${Math.round(freq[i]*100)}%,${DCOL.f} ${Math.round(freq[i]*100)}%)`:DCOL[g[i]];
    return `<div class="rgc ${i===hi?"me":""} ${g[i]==="f"&&!freq?"fo":""}" style="background:${bg}" title="${h}">${h}</div>`}).join("");
  const tot={};DH.forEach((h,i)=>{tot[g[i]]=(tot[g[i]]||0)+dComb(h)});
  const leg=DORDER.split("").filter(l=>tot[l]).map(l=>`<span><i style="background:${DCOL[l]}"></i>${dActLabel(sp,l)} ${(tot[l]/13.26).toFixed(1)}%</span>`).join("");''',
'''  const mx=i=>!freq&&sp.x&&sp.x[i]!=="."?sp.x[i]:null;
  const cells=DH.map((h,i)=>{const m=mx(i);const bg=freq?`linear-gradient(90deg,${DCOL[sp.spot==="rfi"?"j":"c"]} ${Math.round(freq[i]*100)}%,${DCOL.f} ${Math.round(freq[i]*100)}%)`:m?`linear-gradient(135deg,${DCOL[g[i]]} 50%,${DCOL[m]} 50%)`:DCOL[g[i]];
    return `<div class="rgc ${i===hi?"me":""} ${g[i]==="f"&&!freq&&!m?"fo":""} ${m?"mx":""}" style="background:${bg}" title="${h}">${h}</div>`}).join("");
  const tot={};let mxt=0;DH.forEach((h,i)=>{if(mx(i))mxt+=dComb(h);else tot[g[i]]=(tot[g[i]]||0)+dComb(h)});
  const leg=DORDER.split("").filter(l=>tot[l]).map(l=>`<span><i style="background:${DCOL[l]}"></i>${dActLabel(sp,l)} ${(tot[l]/13.26).toFixed(1)}%</span>`).join("")+(mxt?`<span><i class="mxi"></i>섞음(경계) ${(mxt/13.26).toFixed(1)}%</span>`:"");''')
rep('''function dExplain(sp,i){
  const g=dGrid(sp),h=DH[i],r=Math.floor(i/13),c=i%13;
  const play=DH.reduce((s,x,k)=>s+(g[k]!=="f"?dComb(x):0),0)/13.26;''','''function dExplain(sp,i){
  const g=dGrid(sp),h=DH[i],r=Math.floor(i/13),c=i%13,X=k=>sp.x&&sp.x[k]!=="."?sp.x[k]:null;
  const play=DH.reduce((s,x,k)=>s+(g[k]!=="f"?(X(k)==="f"?0.5:1)*dComb(x):(X(k)?0.5*dComb(x):0)),0)/13.26;''')
rep('''  const where=g[i]==="f"?(edge?"레인지 바로 바깥의 경계 핸드":"레인지에서 멀리 떨어진 핸드"):(edge?"레인지 가장자리 핸드":"레인지 안쪽의 확실한 핸드");
  const who=sp.spot==="rfi"?`${sp.st}BB ${sp.pos}에서 첫 진입하는 비율은 전체의 ${play.toFixed(1)}%`:sp.spot==="vs_open"?`40BB BB가 BTN 오픈에 계속 플레이하는 비율은 ${play.toFixed(1)}%`:`${sp.op}의 ${sp.st}BB 올인에 ${sp.pos}가 콜하는 비율은 ${play.toFixed(1)}%`;''',
'''  const where=X(i)?"두 행동을 섞는 경계 핸드":g[i]==="f"?(edge?"레인지 바로 바깥의 경계 핸드":"레인지에서 멀리 떨어진 핸드"):(edge?"레인지 가장자리 핸드":"레인지 안쪽의 확실한 핸드");
  const who=sp.spot==="rfi"?`${sp.st}BB ${sp.pos}에서 첫 진입하는 비율은 전체의 ${play.toFixed(1)}%`:sp.spot==="vs_open"?`${sp.st}BB ${sp.pos}가 ${sp.op} ${sp.op==="SB"?"레이즈":"오픈"}에 계속 플레이하는 비율은 ${play.toFixed(1)}%`:`${sp.op}의 ${sp.st}BB 올인에 ${sp.pos}가 콜하는 비율은 ${play.toFixed(1)}%`;''')
rep('''function dSource(sp){return sp.kind==="chart"?`프리플랍 차트 · ${sp.st}BB`''',
    '''function dSource(sp){return sp.kind==="chart"?`프리플랍 차트 · ${sp.st}BB · 직접 계산 근사와 기준 차트를 합친 것 · 두 색 칸은 섞음`''')
rep('''${sp.kind==="chart"?" · 칸 색은 한 핸드에 한 행동만 칠한 분류예요":" · 칸의 색 비율은 올인/콜 빈도"}''',
    '''${sp.kind==="chart"?" · 한 색 칸은 그 행동, 두 색 칸은 섞는 경계 핸드예요":" · 칸의 색 비율은 올인/콜 빈도"}''')

# 5. 레인지 해설(복기 포함)
rep('''  const w=c.g.split("").map(x=>letters.includes(x)?1:0);if(!w.some(x=>x))return null;
  const n=w.reduce((s,x,i)=>s+x*dComb(DH[i]),0);return{w,key,pg:c.pg,letters,pos,share:n/1326,S};''',
    '''  const w=c.g.split("").map((x,i)=>letters.includes(x)?(c.x[i]==="."?1:0.5):(c.x[i]!=="."&&letters.includes(c.x[i])?0.5:0));if(!w.some(x=>x))return null;
  const n=w.reduce((s,x,i)=>s+x*dComb(DH[i]),0);return{w,key,letters,pos,share:n/1326,S};''')
rep('''function rgCat(P,h){const c=RANGES[P.S][P.hero.key];const L=c?c.g[clsIdx(h.hand)]:"f";return({r:P.hero.key.startsWith("O:")?(P.hero.pos==="SB"?"레이즈":"오픈"):"3벳",j:"올인",c:"콜",l:"림프",f:"폴드"})[L]}''',
    '''function rgCat(P,h){const c=RANGES[P.S][P.hero.key];const i=clsIdx(h.hand),nm=L=>({r:P.hero.key.startsWith("O:")?(P.hero.pos==="SB"?"레이즈":"오픈"):"3벳",j:"올인",c:"콜",l:"림프",f:"폴드"})[L];if(!c)return"폴드";return c.x[i]!=="."?nm(c.g[i])+"·"+nm(c.x[i])+" 섞음":nm(c.g[i])}''')
rep('''  if(c){const sp={kind:"chart",st:S,pos:me,spot:hk.startsWith("O:")?"rfi":"vs_open",g:c.g,pg:c.pg};const Lt=c.g[idx];
    sum.push(["차트",`<b>${cls} → ${dActLabel(sp,Lt)}</b><em>${S}BB ${title} · 히어로 선택 ${lab(d.o,d.k)}</em>`]);
    parts.push(`<p>차트에서 ${cls} 핸드는 <b>${dActLabel(sp,Lt)}</b> 분류이고, ${rgEdge(c.g.split(""),idx)}예요. 히어로 선택은 <b>${lab(d.o,d.k)}</b>.</p>${dMiniGrid(sp,idx)}<p class="rxh">차트 색은 핸드별 분류이고 빈도가 아니에요.</p>`)}''',
    '''  if(c){const sp={kind:"chart",st:S,pos:me,op:v1,spot:hk.startsWith("O:")?"rfi":"vs_open",g:c.g,x:c.x};const Lt=dCellLabel(sp,idx);
    sum.push(["차트",`<b>${cls} → ${Lt}</b><em>${S}BB ${title} · 히어로 선택 ${lab(d.o,d.k)}</em>`]);
    parts.push(`<p>차트에서 ${cls} 핸드는 <b>${Lt}</b> 칸이고, ${c.x[idx]!=="."?"두 행동을 섞는 경계 핸드":rgEdge(c.g.split(""),idx)}예요. 히어로 선택은 <b>${lab(d.o,d.k)}</b>.</p>${dMiniGrid(sp,idx)}<p class="rxh">한 색 칸은 그 행동, 두 색 칸은 섞어서 쓰는 경계 핸드예요.</p>`)}''')
rep('''const R={c:[],st:{}};x.r.w.forEach((y,i)=>{if(y)COMBOS169[i].forEach(cc=>{if(!hs.has(cc[0])&&!hs.has(cc[1]))R.c.push(cc)})});R.ci=R.c.map(z=>[ci(z[0]),ci(z[1])]);return rgPicker(R,R.c.map(()=>1),h,0)''',
    '''const R={c:[],cw:[],st:{}};x.r.w.forEach((y,i)=>{if(y)COMBOS169[i].forEach(cc=>{if(!hs.has(cc[0])&&!hs.has(cc[1])){R.c.push(cc);R.cw.push(y)}})});R.ci=R.c.map(z=>[ci(z[0]),ci(z[1])]);return rgPicker(R,R.cw,h,0)''')
rep('''`<div class="rgc${y?"":" fo"}${i===idx?" me":""}" style="background:${y?col:DCOL.f}"></div>`''',
    '''`<div class="rgc${y?"":" fo"}${i===idx?" me":""}" style="background:${y?col:DCOL.f};${y&&y<1?"opacity:.55":""}"></div>`''')
rep('''const mk=r=>{if(!r)return null;const c=[];r.w.forEach((x,i)=>{if(x)COMBOS169[i].forEach(cc=>c.push(cc))});return{...r,c,ci:c.map(x=>[ci(x[0]),ci(x[1])]),st:{}}};''',
    '''const mk=r=>{if(!r)return null;const c=[],cw=[];r.w.forEach((x,i)=>{if(x)COMBOS169[i].forEach(cc=>{c.push(cc);cw.push(x)})});return{...r,c,cw,ci:c.map(x=>[ci(x[0]),ci(x[1])]),st:{}}};''')
rep('''const st={wH:H?H.c.map(()=>1):null,wV:V.map(R=>R.c.map(c=>hs.has(c[0])||hs.has(c[1])?0:1))};''',
    '''const st={wH:H?H.cw.slice():null,wV:V.map(R=>R.c.map((c,j)=>hs.has(c[0])||hs.has(c[1])?0:R.cw[j]))};''')
rep('''full=R=>R.c.map(c=>hs.has(c[0])||hs.has(c[1])?0:1)''','''full=R=>R.c.map((c,j)=>hs.has(c[0])||hs.has(c[1])?0:(R.cw?R.cw[j]:1))''')

# 5-2. 프리플랍 첫 결정 해설 (gennotes.py 결과) → NOTEFIX에 덮어쓰기
import os
if os.path.exists("notes1102.json"):
    m=re.search(r'const NOTEFIX=(\{.*?\});\n',s);NF=json.loads(m.group(1));NF.update(json.load(open("notes1102.json")))
    s=s[:m.start(1)]+json.dumps(NF,ensure_ascii=False)+s[m.end(1):];print("해설",len(json.load(open("notes1102.json"))),"개 반영")

# 6. 섞음 칸 스타일
rep('</style>','.rgc.mx{opacity:.82}.rleg i.mxi{background:linear-gradient(135deg,#D9A13B 50%,#1A2536 50%)}\n</style>',1) if s.count('</style>')==1 else None

# 7. 통합 GTO 차트 문구 + 읽기 쉬운 믹스 칸 (11/3 사용자 요청: 솔버·기준 차트 구분 없이 통합 차트, 홀덤 용어, 100-75BB 공통)
#    믹스 칸: 두 액션을 반씩 칠함(왼쪽 = 더 공격적인 액션, 가운데 검은 선)
rep('function dCellLabel(sp,i){const x=sp.x&&sp.x[i]!=="."?sp.x[i]:null;return x?`${dActLabel(sp,sp.g[i])}·${dActLabel(sp,x)} 섞음`:dActLabel(sp,sp.g[i])}',
    'function dCellLabel(sp,i){const x=sp.x&&sp.x[i]!=="."?sp.x[i]:null;return x?`${dActLabel(sp,sp.g[i])}·${dActLabel(sp,x)} 믹스`:dActLabel(sp,sp.g[i])}\n// 통합 차트 스택 표기: 75 칸은 100-75BB 공통\nfunction stLab(S){return S===75?"100-75BB":S+"BB"}')
rep('m?`linear-gradient(135deg,${DCOL[g[i]]} 50%,${DCOL[m]} 50%)`','m?`linear-gradient(90deg,${g[i]==="f"?"#3E465A":DCOL[g[i]]} 0 47%,#0B0E16 47% 53%,${m==="f"?"#3E465A":DCOL[m]} 53% 100%)`')
rep('(mxt?`<span><i class="mxi"></i>섞음(경계) ${(mxt/13.26).toFixed(1)}%</span>`:"");\n  return `<div class="rgw"><div class="rg">${cells}</div></div><div class="rleg">${leg}</div>`;',
    '(mxt?`<span><i class="mxi"></i>믹스 ${(mxt/13.26).toFixed(1)}%</span>`:"");\n  return `<div class="rgw"><div class="rg">${cells}</div></div><div class="rleg">${leg}</div>`+(mxt?`<p class="rhint">믹스: 두 액션을 섞는 경계 핸드예요.</p>`:"");')
rep('.rgc.mx{opacity:.82}.rleg i.mxi{background:linear-gradient(135deg,#D9A13B 50%,#1A2536 50%)}',
    '.rgc{text-shadow:0 1px 1px rgba(0,0,0,.55)}.rgc.mx{text-shadow:0 1px 2px #000,0 0 3px #000;font-weight:700}.rleg i.mxi{background:linear-gradient(90deg,#D9A13B 0 45%,#0B0E16 45% 55%,#3E465A 55% 100%)}.rhint{margin:6px 0 0;font-size:12px;color:var(--muted);line-height:1.5}')
# 해설 문장 (솔버 기준, 홀덤 용어)
rep('verdict=`차트에서 ${cls} 핸드는 <b>${dCellLabel(sp,idx)}</b>`+(sp.x[idx]!=="."?`. 직접 계산과 기준 차트가 갈리는 경계 핸드라 두 행동을 비슷하게 섞어요`:"")+(sp.multi?`. 앞에 콜러가 있어 1:1 대응 차트로 근사했어요`:"");',
    'verdict=`통합 차트에서 ${cls}는 <b>${dCellLabel(sp,idx)}</b>`+(sp.x[idx]!=="."?`. 두 액션을 섞는 경계 핸드예요`:"")+(sp.multi?`. 앞에 콜러가 있어 1:1 오픈 대응 차트로 근사했어요`:"");')
rep('verdict=`${sp.st}BB ${sp.kind==="hu"?"헤즈업 ":""}계산 근사에서 ${cls} 핸드는 <b>',
    'verdict=`${sp.st}BB ${sp.kind==="hu"?"헤즈업 ":""}푸시/폴드 계산에서 ${cls}는 <b>')
rep('verdict+=`. ${go}과 폴드의 EV 차이가 ${Math.abs(ev).toFixed(2)}BB로 거의 같아서, 계산 방법에 따라 섞는 비율이 크게 달라질 수 있는 경계 핸드예요`;',
    'verdict+=`. ${go}과 폴드의 EV 차이가 ${Math.abs(ev).toFixed(2)}BB로 거의 같은 경계 핸드예요`;')
rep('verdict+=`. 이 계산은 올인과 폴드만 비교해서, 작은 레이즈 선택지는 들어 있지 않아요`',
    'verdict+=`. 이 계산은 잼/폴드만 비교해서 미니레이즈는 들어 있지 않아요`')
rep('`<p class="warn2">이 핸드는 ${h.d||100}BB라 정확히 맞는 차트가 없어요. 가장 가까운 ${ref.from}BB ${sp.kind==="chart"?"프리플랍 차트":"계산 근사"}를 참고용으로만 보여줘요. 스택이 다르면 정답도 달라질 수 있어요.</p>`',
    '`<p class="warn2">${h.d||100}BB ${sp.kind==="chart"?"차트":"계산"}가 없어 가장 가까운 ${sp.kind==="chart"?stLab(ref.from)+" 통합 차트":ref.from+"BB 계산"}를 보여 줘요. 스택이 다르면 레인지도 달라질 수 있어요.</p>`')
rep('<b>프리플랍 차트 · ${sp.st}BB ${sp.pos}${sp.spot==="vs_open"?" vs "+sp.op+(sp.op==="SB"?" 레이즈":" 오픈"):sp.spot==="vs_shove"?" vs "+sp.op+" 올인":" 첫 진입"}</b>',
    '<b>프리플랍 차트 · ${sp.kind==="chart"?stLab(sp.st):sp.st+"BB"} ${sp.pos}${sp.spot==="vs_open"?" vs "+sp.op+(sp.op==="SB"?" 레이즈":" 오픈"):sp.spot==="vs_shove"?" vs "+sp.op+" 올인":" RFI"}</b>')
rep('''  const where=X(i)?"두 행동을 섞는 경계 핸드":g[i]==="f"?(edge?"레인지 바로 바깥의 경계 핸드":"레인지에서 멀리 떨어진 핸드"):(edge?"레인지 가장자리 핸드":"레인지 안쪽의 확실한 핸드");
  const who=sp.spot==="rfi"?`${sp.st}BB ${sp.pos}에서 첫 진입하는 비율은 전체의 ${play.toFixed(1)}%`:sp.spot==="vs_open"?`${sp.st}BB ${sp.pos}가 ${sp.op} ${sp.op==="SB"?"레이즈":"오픈"}에 계속 플레이하는 비율은 ${play.toFixed(1)}%`:`${sp.op}의 ${sp.st}BB 올인에 ${sp.pos}가 콜하는 비율은 ${play.toFixed(1)}%`;
  return `${who}이고, ${h} 핸드는 ${where}예요.`;''',
'''  const where=X(i)?"두 액션을 섞는 경계 핸드":g[i]==="f"?(edge?"레인지 바로 밖의 경계 핸드":"레인지 밖의 확실한 폴드"):(edge?"레인지 가장자리 핸드":"레인지 안쪽 핸드");
  const who=sp.spot==="rfi"?`${sp.kind==="chart"?stLab(sp.st):sp.st+"BB"} ${sp.pos} RFI 레인지는 ${play.toFixed(1)}%`:sp.spot==="vs_open"?`${stLab(sp.st)} ${sp.pos}의 vs ${sp.op} ${sp.op==="SB"?"레이즈":"오픈"} 디펜스(콜+3벳)는 ${play.toFixed(1)}%`:`${sp.op} ${sp.st}BB 올인에 ${sp.pos} 콜 레인지는 ${play.toFixed(1)}%`;
  return `${who}이고, ${h}는 ${where}예요.`;''')
rep('function dSource(sp){return sp.kind==="chart"?`프리플랍 차트 · ${sp.st}BB · 직접 계산 근사와 기준 차트를 합친 것 · 두 색 칸은 섞음`',
    'function dSource(sp){return sp.kind==="chart"?`${stLab(sp.st)} 통합 GTO 차트 · 9인 BB 앤티 · 두 색 칸은 믹스`')
rep('${sp.kind==="chart"?" · 한 색 칸은 그 행동, 두 색 칸은 섞는 경계 핸드예요":" · 칸의 색 비율은 올인/콜 빈도"}',
    '${sp.kind==="chart"?" · 두 색 칸은 믹스":" · 칸의 색 비율은 잼/콜 빈도"}')
# 핸드 복기 쪽 문장
rep('return g[i]==="f"?(edge?"레인지 바로 바깥의 경계 핸드":"레인지에서 멀리 떨어진 핸드"):(edge?"레인지 가장자리 핸드":"레인지 안쪽의 확실한 핸드")}',
    'return g[i]==="f"?(edge?"레인지 바로 밖의 경계 핸드":"레인지 밖의 확실한 폴드"):(edge?"레인지 가장자리 핸드":"레인지 안쪽 핸드")}')
rep('${c.x[idx]!=="."?"두 행동을 섞는 경계 핸드":rgEdge(c.g.split(""),idx)}예요','${c.x[idx]!=="."?"두 액션을 섞는 경계 핸드":rgEdge(c.g.split(""),idx)}예요')
rep('<p class="rxh">한 색 칸은 그 행동, 두 색 칸은 섞어서 쓰는 경계 핸드예요.</p>','<p class="rxh">두 색 칸은 두 액션을 섞는 믹스 핸드예요.</p>')
rep('return c.x[i]!=="."?nm(c.g[i])+"·"+nm(c.x[i])+" 섞음":nm(c.g[i])}','return c.x[i]!=="."?nm(c.g[i])+"·"+nm(c.x[i])+" 믹스":nm(c.g[i])}')
rep('sum.push(["차트",`<b>${cls} → ${Lt}</b><em>${S}BB ${title}','sum.push(["GTO 차트",`<b>${cls} → ${Lt}</b><em>${stLab(S)} ${title}')
rep('<p>차트에서 ${cls} 핸드는 <b>${Lt}</b> 칸이고,','<p>통합 차트에서 ${cls}는 <b>${Lt}</b> 칸이고,')

# 8. 하단 메뉴 '차트' 탭 (11/4 적용): 통합 GTO 차트(15·25·40·100-75BB)와 푸시/폴드 계산(8~20BB)을 포지션별로 보기
rep('''const MNAV_IC={home:'<path d="M3 10l8-7 8 7v9H3z"></path>',rank:'<path d="M5 19V9M11 19V3M17 19v-7"></path>',''',
    '''const MNAV_IC={home:'<path d="M3 10l8-7 8 7v9H3z"></path>',rank:'<path d="M5 19V9M11 19V3M17 19v-7"></path>',chart:'<rect x="3" y="3" width="16" height="16" rx="2"></rect><path d="M3 9h16M3 15h16M9 3v16M15 3v16"></path>',''')
rep('[["home","홈"],["rank","순위"],["coach","코치"],["more","더보기"]]','[["home","홈"],["rank","순위"],["chart","차트"],["coach","코치"],["more","더보기"]]')
rep('.mnav{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:min(100%,420px);box-sizing:border-box;z-index:20;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));',
    '.mnav{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:min(100%,420px);box-sizing:border-box;z-index:20;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));')
rep('''  if(MENUTAB==="more"){
    const tg=tierGuideHTML();''','''  if(MENUTAB==="chart"){
    $("panel").innerHTML=`<div class="ctab" id="ctab"></div>${menuNav("chart")}`;
    menuNavBind();ctabRender();return}
  if(MENUTAB==="more"){
    const tg=tierGuideHTML();''')
rep('function myRankText(){',r'''// ===== 차트 탭: 통합 GTO 차트 보기 =====
let CT={mode:"rfi",st:40,pos:"UTG",op:"UTG",def:"BB",pf:10,pfk:"jam",pop:"UTG",sel:-1};
const CT_POS=["UTG","UTG+1","UTG+2","LJ","HJ","CO","BTN","SB"];
const CT_OPS=[["UTG","UTG"],["LJ/HJ","LJ·HJ"],["CO","CO"],["BTN","BTN"]];
function ctDefs(S,op){const R=RANGES[S]||{},out=[];Object.keys(R).forEach(k=>{if(!k.startsWith("D:"))return;const [d,o]=k.slice(2).split("<");if(o===op||(op==="LJ/HJ"&&o==="LJ"))out.push([k,d==="LJ/HJ"?"LJ·HJ":d==="UTG+1/+2"?"UTG+1·+2":d])});
  const ord=["UTG+1·+2","LJ·HJ","HJ","CO","BTN","SB","BB"];return out.sort((a,b)=>ord.indexOf(a[1])-ord.indexOf(b[1]))}
function ctSeg(id,items,cur){return `<div class="cseg" id="${id}">${items.map(([v,t])=>`<button type="button" data-v="${esc(String(v))}" class="${String(v)===String(cur)?"on":""}" ${String(v)===String(cur)?'aria-pressed="true"':'aria-pressed="false"'}>${t}</button>`).join("")}</div>`}
function ctSpot(){
  if(CT.mode==="pf"){const P=DRILL_PF[CT.pf];
    if(CT.pfk==="jam")return{sp:{kind:"pf",st:CT.pf,pos:CT.pos==="BB"?"SB":CT.pos,spot:"rfi"},title:`${CT.pf}BB ${CT.pos} 잼(첫 진입)`};
    const ks=Object.keys(P.call).filter(k=>k.split(">")[0]===CT.pop);let k=ks.find(x=>x.split(">")[1]===CT.def)||ks[0];if(!k)return null;const [op,pos]=k.split(">");CT.def=pos;
    return{sp:{kind:"pf",st:CT.pf,pos,op,spot:"vs_shove"},title:`${CT.pf}BB ${pos} vs ${op} 잼 콜`,defs:ks.map(x=>x.split(">")[1])}}
  const S=CT.st,R=RANGES[S]||{};
  if(CT.mode==="rfi"){const c=R["O:"+CT.pos];return c?{sp:{kind:"chart",st:S,pos:CT.pos,spot:"rfi",g:c.g,x:c.x},title:`${stLab(S)} ${CT.pos} RFI`}:null}
  if(CT.mode==="bvs"){const c=R["D:BB<SB"];return c?{sp:{kind:"chart",st:S,pos:"BB",op:"SB",spot:"vs_open",g:c.g,x:c.x},title:`${stLab(S)} BB vs SB 레이즈`}:null}
  const defs=ctDefs(S,CT.op);let d=defs.find(x=>x[1]===CT.def)||defs.find(x=>x[1]==="BB")||defs[0];if(!d)return null;CT.def=d[1];const c=R[d[0]];
  return{sp:{kind:"chart",st:S,pos:d[1],op:CT.op==="LJ/HJ"?"LJ·HJ":CT.op,spot:"vs_open",g:c.g,x:c.x},title:`${stLab(S)} ${d[1]} vs ${CT.op==="LJ/HJ"?"LJ·HJ":CT.op} 오픈`,defs:defs.map(x=>x[1])}
}
function ctabRender(){
  const el=$("ctab");if(!el)return;
  const modes=[["rfi","RFI"],["vso","vs 오픈"],["bvs","BB vs SB"],["pf","푸시/폴드"]];
  let stacks=CT.mode==="pf"?PFST.map(s=>[s,s+"BB"]):[15,25,40,75].filter(s=>CT.mode!=="bvs"||(RANGES[s]||{})["D:BB<SB"]).map(s=>[s,stLab(s)]);
  if(CT.mode!=="pf"&&!stacks.some(x=>x[0]===CT.st))CT.st=stacks[stacks.length-1][0];
  const r=ctSpot();let rows="";
  if(CT.mode==="rfi")rows=`<div class="crow"><span>히어로</span>${ctSeg("ctPos",CT_POS.map(p=>[p,p]),CT.pos)}</div>`;
  else if(CT.mode==="vso")rows=`<div class="crow"><span>오프너</span>${ctSeg("ctOp",CT_OPS,CT.op)}</div><div class="crow"><span>히어로</span>${ctSeg("ctDef",(r&&r.defs||[]).map(d=>[d,d]),CT.def)}</div>`;
  else if(CT.mode==="pf"){rows=`<div class="crow"><span>상황</span>${ctSeg("ctPfk",[["jam","잼(첫 진입)"],["call","잼에 콜"]],CT.pfk)}</div>`+
    (CT.pfk==="jam"?`<div class="crow"><span>히어로</span>${ctSeg("ctPos",CT_POS.map(p=>[p,p]),CT.pos)}</div>`:`<div class="crow"><span>잼</span>${ctSeg("ctPop",DPOS.slice(0,8).map(p=>[p,p]),CT.pop)}</div><div class="crow"><span>히어로</span>${ctSeg("ctDef",(r&&r.defs||[]).map(d=>[d,d]),CT.def)}</div>`)}
  let det="";
  if(r&&CT.sel>=0){const sp=r.sp,i=CT.sel,h=DH[i];
    if(sp.kind==="chart")det=`<b>${h}</b><span class="cact">${dCellLabel(sp,i)}</span><p>${dExplain(sp,i)}</p>`;
    else{const f=pfF(sp)[i],ev=pfE(sp)[i],go=sp.spot==="rfi"?"잼":"콜";det=`<b>${h}</b><span class="cact">${go} ${Math.round(f*100)}% · 폴드 ${Math.round((1-f)*100)}%</span><p>${go} EV ${ev>=0?"+":""}${ev.toFixed(2)}BB · 폴드 0BB. ${dExplain(sp,i)}</p>`}}
  el.innerHTML=`<div class="chd"><b>GTO 차트</b><small>통합 GTO 차트 · 9인 BB 앤티</small></div>
    ${ctSeg("ctMode",modes,CT.mode)}${ctSeg("ctSt",stacks,CT.mode==="pf"?CT.pf:CT.st)}${rows}
    ${r?`<div class="cbox"><div class="ctt">${esc(r.title)}</div>${dMiniGrid(r.sp,CT.sel)}<p class="note">${dSource(r.sp)}</p></div>
    <div class="cdet" id="ctDet">${det||'<span class="cmuted">핸드를 누르면 액션과 해설이 나와요.</span>'}</div>`:`<div class="cbox"><p class="cmuted">이 스택에는 차트가 없어요.</p></div>`}`;
  const on=(id,f)=>{const g=$(id);if(g)g.querySelectorAll("button").forEach(b=>b.onclick=()=>{f(b.dataset.v);CT.sel=-1;ctabRender()})};
  on("ctMode",v=>{CT.mode=v;if(v==="bvs")CT.st=40});on("ctSt",v=>{if(CT.mode==="pf")CT.pf=+v;else CT.st=+v});
  on("ctPos",v=>CT.pos=v);on("ctOp",v=>{CT.op=v;CT.def="BB"});on("ctDef",v=>CT.def=v);on("ctPfk",v=>CT.pfk=v);on("ctPop",v=>{CT.pop=v;CT.def="BB"});
  el.querySelectorAll(".rg .rgc").forEach((c,i)=>{c.style.cursor="pointer";c.onclick=()=>{CT.sel=i;ctabRender();const d=$("ctDet");if(d&&d.scrollIntoView)d.scrollIntoView({block:"nearest"})}});
}
function myRankText(){''')
rep('</style>','.ctab{display:flex;flex-direction:column;gap:10px;padding-bottom:8px}.chd{display:flex;flex-direction:column;gap:2px}.chd b{font-size:19px}.chd small{font-size:12px;color:var(--muted)}'
    '.cseg{display:flex;flex-wrap:wrap;gap:6px}.cseg button{min-height:36px;padding:0 11px;border-radius:10px;border:1px solid #1F2A3F;background:#0E1626;color:#A9B2C3;font-size:13px;font-weight:600;font-family:inherit}'
    '.cseg button.on{background:#231D13;border-color:rgba(212,175,124,.7);color:#F0D7AE;font-weight:800}'
    '.crow{display:flex;align-items:flex-start;gap:8px}.crow>span{flex:none;width:40px;padding-top:9px;font-size:11px;color:var(--muted)}.crow .cseg{flex:1}'
    '.cbox{border:1px solid rgba(212,175,124,.3);border-radius:16px;padding:12px;background:#0B1220;display:flex;flex-direction:column;gap:8px}.ctt{font-weight:800;font-size:14px}'
    '.cdet{border-radius:14px;padding:12px;background:#121A2B;display:flex;flex-direction:column;gap:4px;font-size:13px;line-height:1.55}.cdet b{font-family:var(--mono);font-size:18px}.cact{color:#F0D7AE;font-weight:800}.cdet p{margin:0;color:#C9D0DC}.cmuted{color:var(--muted);font-size:13px}'
    '.rg{min-width:0}.rgc{font-size:clamp(7px,2.1vw,9px);letter-spacing:-.02em} /* 13칸 차트가 폰 폭에서 잘리지 않게(예전엔 최소 300px라 390폭에서 오른쪽 한 줄이 가려짐) */\n</style>',1)

# 남은 강의 흔적 확인
left=[m.group(0) for m in re.finditer(r'.{30}(교재|강의|PDF|pg:c\.pg|pfChartLetter|DRILL_CHARTS).{30}',s)]
print("남은 표기",len(left));[print("  ",x) for x in left[:20]]
open(dst,"w",encoding="utf-8").write(s);print("저장",dst,len(s))
