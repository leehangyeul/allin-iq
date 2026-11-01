# 11/1 점검 수정: 헤즈업 문제 해설은 헤즈업(앤티 없음) 계산으로, 하단 안내 문구 정리
import sys
p=sys.argv[1];S=open(p,encoding="utf-8").read()
def rep(a,b):
    global S
    assert S.count(a)==1,(S.count(a),a[:70]);S=S.replace(a,b)
rep("""const pfF=sp=>sp.spot==="rfi"?DRILL_PF[sp.st].jam[sp.pos]:DRILL_PF[sp.st].call[sp.op+">"+sp.pos];
const pfE=sp=>sp.spot==="rfi"?DRILL_PF[sp.st].jam_ev[sp.pos]:DRILL_PF[sp.st].call_ev[sp.op+">"+sp.pos];""",
"""// 헤즈업 푸시/폴드(앤티 없음, HU_EV): 올인/콜 EV가 폴드보다 크면 그 행동
const huE=sp=>{const r=(HU_EV[String(sp.st)]||{})[sp.spot==="rfi"?"sb":"bb"]||{};return DH.map(c=>+r[c]||0)};
const pfF=sp=>sp.kind==="hu"?huE(sp).map(x=>x>0?1:0):sp.spot==="rfi"?DRILL_PF[sp.st].jam[sp.pos]:DRILL_PF[sp.st].call[sp.op+">"+sp.pos];
const pfE=sp=>sp.kind==="hu"?huE(sp):sp.spot==="rfi"?DRILL_PF[sp.st].jam_ev[sp.pos]:DRILL_PF[sp.st].call_ev[sp.op+">"+sp.pos];
const isHU=h=>HEV.indexOf(h.me+"|"+h.hand.join(""))>=0&&!!HU_EV[String(h.d||100)];""")
rep("""function dSource(sp){return sp.kind==="chart"?`프리플랍 차트 · ${sp.st}BB`:`${sp.st}BB 직접 계산 근사 · 9인 BB 앤티 · 첫 콜러 모델 · cEV`}""",
"""function dSource(sp){return sp.kind==="chart"?`프리플랍 차트 · ${sp.st}BB`:sp.kind==="hu"?`${sp.st}BB 헤즈업 직접 계산 근사 · 앤티 없음 · cEV`:`${sp.st}BB 직접 계산 근사 · 9인 BB 앤티 · 첫 콜러 모델 · cEV`}""")
rep("""  if(sp.kind==="pf")freq=pfF(sp);""","""  if(sp.kind!=="chart")freq=pfF(sp);""")
rep("""function chartRef(h){
  const D=h.d||100,me=QPOS(h.me),pf=h.pf;const unopened=pf[1]<=1;""","""function chartRef(h){
  const D=h.d||100,me=QPOS(h.me),pf=h.pf;const unopened=pf[1]<=1;
  if(isHU(h))return{sp:h.me==="SB"?{kind:"hu",st:D,pos:"SB",spot:"rfi"}:{kind:"hu",st:D,pos:"BB",op:"SB",spot:"vs_shove"},exact:true,from:D};""")
rep("""  else{const f=pfF(sp)[idx];verdict=`${sp.st}BB 계산 근사에서""","""  else{const f=pfF(sp)[idx];verdict=`${sp.st}BB ${sp.kind==="hu"?"헤즈업 ":""}계산 근사에서""")
rep("""  if(h.cv&&d){const ref=chartRef(h);""","""  if((h.cv||isHU(h))&&d){const ref=chartRef(h);""")
rep("""<em>${sp.st}BB 계산 근사 · ${go} EV""","""<em>${sp.st}BB ${sp.kind==="hu"?"헤즈업 ":""}계산 근사 · ${go} EV""")
rep("""<p class="disc">GTO 빈도는 앱 구조를 보여주기 위한 예시 수치예요. 실제 버전은 솔버 결과로 교체합니다.</p>""",
"""<p class="disc">오픈 연습과 짧은 스택 올인·콜 문제는 직접 계산한 근사값이고, 그 밖의 핸드 퀴즈 빈도는 GTO 감각을 익히기 위한 예시 수치예요.</p>""")
open(p,"w",encoding="utf-8").write(S);print("ok")
# (2) 계산 참고 차트에 EV와 '거의 같음' 안내, 레이즈 선택지가 있는 문제엔 '올인/폴드만 비교' 안내
S=open(p,encoding="utf-8").read()
a="""  else{const f=pfF(sp)[idx];verdict=`${sp.st}BB ${sp.kind==="hu"?"헤즈업 ":""}계산 근사에서 ${cls} 핸드는 <b>${sp.spot==="rfi"?"올인":"콜"} ${(f*100).toFixed(1)}%</b>`}"""
b="""  else{const f=pfF(sp)[idx],ev=pfE(sp)[idx],go=sp.spot==="rfi"?"올인":"콜";verdict=`${sp.st}BB ${sp.kind==="hu"?"헤즈업 ":""}계산 근사에서 ${cls} 핸드는 <b>${go} ${Math.round(f*100)}%</b> (${go} EV ${ev>=0?"+":""}${ev.toFixed(2)}BB, 폴드 0BB)`;
    if(Math.abs(ev)<0.3)verdict+=`. ${go}과 폴드의 EV 차이가 ${Math.abs(ev).toFixed(2)}BB로 거의 같아서, 계산 방법에 따라 섞는 비율이 크게 달라질 수 있는 경계 핸드예요`;
    if((h.s[0].o||[]).some(x=>x[0]==="raise"||/^b\\d+$/.test(x[0])))verdict+=`. 이 계산은 올인과 폴드만 비교해서, 작은 레이즈 선택지는 들어 있지 않아요`}"""
assert S.count(a)==1;S=S.replace(a,b)
open(p,"w",encoding="utf-8").write(S);print("ok2")
# (3) 헤즈업 계산은 빈도가 아니라 EV만 있어요: EV가 0에 가까우면 '거의 같음'으로 표시
S=open(p,encoding="utf-8").read()
a='''<b>${DH[i]} → ${go} ${Math.round(f*100)}%</b>'''
b='''<b>${DH[i]} → ${sp.kind==="hu"&&Math.abs(ev)<0.05?go+"·폴드 거의 같음":go+" "+Math.round(f*100)+"%"}</b>'''
assert S.count(a)==1;S=S.replace(a,b)
a='''핸드는 <b>${go} ${Math.round(f*100)}%</b> (${go} EV'''
b='''핸드는 <b>${sp.kind==="hu"&&Math.abs(ev)<0.05?go+"과 폴드가 거의 같음":go+" "+Math.round(f*100)+"%"}</b> (${go} EV'''
assert S.count(a)==1;S=S.replace(a,b)
open(p,"w",encoding="utf-8").write(S);print("ok3")
