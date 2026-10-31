# 핸드 퀴즈 해설이 정답(가장 높은 빈도)과 반대 행동을 권하지 않는지: "X이/가 기본", "X로 싸게 플랍", "X이 Y보다 좋아요" 같은 문장을 정답과 대조
import asyncio,sys,os,re,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
G={'폴드':'F','접':'F','콜':'C','림프':'C','체크':'K','레이즈':'A','3벳':'A','4벳':'A','5벳':'A','올인':'A','오픈':'A','베팅':'A','리스틸':'A'}
W='(폴드|콜|림프|체크|레이즈|3벳|4벳|5벳|올인|오픈|베팅|리스틸)'
def top_group(k):return {'fold':'F','call':'C','check':'K'}.get(k,'A')
def claims(n):
    out=[]
    for m in re.finditer(W+r'(?:이|가|을|를|은|는)?\s?(?:기본|정답)',n):
        if '지만' in n[m.end():m.end()+3]:continue      # "콜이 기본이지만 3벳도 섞어" 같은 문장은 아래에서 따로
        out.append(G[m.group(1)])
    for m in re.finditer(W+r'(?:으로|로) 싸게',n):out.append(G[m.group(1)])
    for m in re.finditer(W+r'(?:이|가)\s?'+W+r'보다 (?:조금 )?(?:더 )?(?:좋|이득)',n):out.append(G[m.group(1)])
    for m in re.finditer(W+r'(?:이|가) 기본이지만',n):out.append(G[m.group(1)])
    return out
async def main():
    srv=start_server();bad=[]
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page()
        await pg.goto('http://127.0.0.1:8765/index.html');await asyncio.sleep(1.5)
        r=await pg.evaluate("""()=>{const out=[];LEVELS.forEach(L=>L.hands.forEach((h,hi)=>{const k=String(h.key||'');if(/콜보다 3벳 아니면 폴드|셋 마이닝보다 3벳 올인이 좋을/.test(k))out.push({hi,si:-1,me:h.me,hand:h.hand.join(''),top:'key',p:0,n:k})}));LEVELS.forEach(L=>L.hands.forEach((h,hi)=>(h.s||[]).forEach((s,si)=>{const f=s.f||{};const ks=Object.keys(f);const top=ks.reduce((a,b)=>(+f[b]||0)>(+f[a]||0)?b:a);
          out.push({hi,si,me:h.me,hand:h.hand.join(''),top,p:+f[top]||0,n:String(s.n||'')})})));return {out,fixed:typeof noteFix==='function'?noteFix():-1,keys:typeof NOTEFIX==='object'?Object.keys(NOTEFIX).length:0}}""")
        kk=await pg.evaluate("()=>LEVELS[0].hands.filter(h=>KEYFIX[h.me+'|'+h.hand.join('')]===h.key).length===Object.keys(KEYFIX).length")
        if not kk:bad.append('핸드 핵심 문장 고침이 적용되지 않음')
        if r['fixed']!=r['keys'] or r['keys']==0:bad.append(f"해설 고침 목록 {r['keys']}개 중 {r['fixed']}개만 적용")
        for x in r['out']:
            if x['top']=='key':
                # 핵심 문장 금지 패턴: 해당 핸드의 첫 결정 정답이 콜이면 모순
                bad.append(f"#{x['hi']} 핵심 문장 확인 필요: {x['n'][:40]}");continue
            tg=top_group(x['top'])
            for c in claims(x['n']):
                if c!=tg:bad.append(f"#{x['hi']}-{x['si']} {x['me']} {x['hand']}: 정답 {x['top']} {x['p']}% / 해설 '{x['n'][:40]}'");break
    print('OK' if not bad else 'FAIL '+str(len(bad))+' '+str(bad[:8]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
