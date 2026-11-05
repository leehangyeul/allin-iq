# 계산 모드(11/6): 대본과 다른 선택을 하면 남은 스트리트가 레인지 계산으로 진행되는지, OOP 첫 행동 노드, 빌런 폴드·콜·올인 반응,
# 3벳 뒤 빌런(콜러)이 플랍에서 먼저 베팅하지 않는지, 점수·화면에 NaN 없는지
import asyncio,sys,os,random,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    random.seed(11);srv=start_server();store['meta/season']={'v':0};bad=[];st=collections.Counter()
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn');await asyncio.sleep(1)
        n=await pg.evaluate("()=>{start(0);return LEVELS[0].hands.length}")
        idx=[i for i in range(n)]
        for i in idx:
            for path in range(3):
                await pg.evaluate("(i)=>{start(0);order[hi]=LEVELS[0].hands[i];newHand()}",i)
                for step in range(25):
                    info=await pg.evaluate("()=>{const c=G.sub||G.cur;if(!document.querySelector('#panel button[data-k]'))return null;const mo=mergedOF(c);const top=bestOf(mo.o,mo.f);return{keys:[...document.querySelectorAll('#panel button[data-k]')].map(x=>x.dataset.k),top,first:!!c.first,cx:!!G.cx,a:c.a||'',si,label:c.label}}")
                    if not info:break
                    if info['first']:st['첫 행동 노드']+=1
                    if info['cx']:st['계산 모드 결정']+=1
                    if path==0:k=next((x for x in info['keys'] if x!=info['top']),info['keys'][0])   # 1순위가 아닌 선택
                    elif path==1:k=next((x for x in info['keys'] if x.startswith('b') or x in('raise','jam')),info['keys'][0])  # 공격적으로
                    else:k=random.choice(info['keys'])
                    await pg.evaluate("(k)=>document.querySelector('#panel button[data-k=\"'+k+'\"]').click()",k)
                r=await pg.evaluate("""()=>{const t=document.getElementById('panel').innerText+document.getElementById('stage').innerText+document.getElementById('top').innerText;
                  const big=(document.querySelector('.scr .big')||{}).innerText||'';
                  // 3벳(히어로 공격자) 뒤 계산 모드에서 빌런이 플랍에 먼저 베팅했는지
                  const pre=G.dec[0];const donk=G.cx&&pre&&(pre.k==='raise')&&G.dec.some(d=>d.si===1&&d.cx&&/^빌런 \\d+% 베팅|^빌런 올인/.test(d.a));
                  return{big,ended:G.ended,cx:G.cx,dec:G.dec.length,vr:G.dec.map(d=>d.vr).filter(Boolean),nan:/NaN|undefined|\\[object/.test(t),donk,ws:G.dec.map(d=>d.w)}}""")
                if not r['big']:bad.append(f'핸드 {i} 경로{path}: 결과 없음 (결정 {r["dec"]})');continue
                sc=int(r['big'].split('/')[0].strip())
                if not 0<=sc<=100:bad.append(f'핸드 {i} 점수 {sc}')
                if r['nan']:bad.append(f'핸드 {i} 경로{path}: NaN/undefined')
                if r['donk']:bad.append(f'핸드 {i}: 3벳 뒤 계산 모드에서 빌런이 플랍 리드')
                if r['cx']:st['계산 모드 핸드']+=1
                for v in r['vr']:st[v.split(' (')[0]]+=1
                if r['ended']=='vfold':st['빌런 폴드로 끝']+=1
                if 0.3 in r['ws']:st['비중 0.3 결정 포함']+=1
        errs=[e for e in pg.errs if 'ERR_FAILED' not in e];bad+=errs[:5]
        # 화면 확인용 스크린샷: 계산 모드 핸드 하나
        await pg.set_viewport_size({'width':390,'height':844})
    print(dict(st))
    print('OK' if not bad else 'FAIL '+str(len(bad))+' '+str(bad[:12]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
