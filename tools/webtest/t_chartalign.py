# 프리플랍 첫 결정: 정답(가장 높은 빈도)이 교재 차트 분류와 같은 방향인지 (림프 차트인데 선택지에 림프 없는 SB 단스택 2건은 예외)
import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[];tot=0
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1)
        r=await pg.evaluate("""()=>{start(0);const out=[];LEVELS[0].hands.forEach(h=>{const L=pfChartLetter(h);if(!L)return;const f=h.s[0].f,keys=h.s[0].o.map(x=>x[0]);
          const g=k=>+f[k]||0,isR=k=>k==='raise'||/^b\\d+$/.test(k);const tk=L==='f'?'fold':L==='j'?'jam':(L==='c'||L==='l')?'call':(keys.find(isR)||'jam');
          if(!keys.includes(tk))return;const mx=Math.max(...keys.map(g));out.push({id:h.me+' '+h.hand.join(''),L,ok:g(tk)===mx})});return out}""")
        tot=len(r);bad=[x['id']+' 차트 '+x['L'] for x in r if not x['ok']]
    print(f'차트 대응 {tot}개 확인');print('FAIL '+str(bad[:10]) if bad else 'OK');srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
