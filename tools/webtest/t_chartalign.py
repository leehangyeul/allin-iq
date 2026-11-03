# 프리플랍 첫 결정: 정답(가장 높은 빈도)이 합친 프리플랍 차트와 같은지
# 한 행동 칸 → 그 행동이 60% 이상 확실한 1위. 섞음 칸 → 두 행동이 1·2위이고 차이 10%p 이하. 해설 차트 칸과 같은 함수(chartCell)를 써요.
import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[];tot=0
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1)
        r=await pg.evaluate("""()=>{start(0);const out=[];LEVELS[0].hands.forEach(h=>{const c=chartCell(h);if(!c)return;const f=h.s[0].f,keys=h.s[0].o.map(x=>x[0]);
          const g=k=>+f[k]||0;let ta=chartOptKey(keys,c.a,c.spot==='vs_open'),tb=c.b?chartOptKey(keys,c.b,true):null;if(!ta){ta=tb;tb=null}if(!ta)return;if(tb===ta)tb=null;
          const srt=keys.slice().sort((x,y)=>g(y)-g(x));let ok=g(ta)===g(srt[0]);
          if(tb)ok=ok&&g(tb)===g(srt[1])&&g(ta)-g(tb)<=10;
          else ok=ok&&g(ta)>=60&&g(ta)>g(srt[1]);   // 한 행동 칸은 확실한 1위
          const ref=chartRef(h);const shown=ref&&ref.sp.kind==='chart'&&ref.sp.g===c.g;
          out.push({id:h.me+' '+h.hand.join(''),L:c.a+(c.b||''),ok:ok&&shown})});return out}""")
        tot=len(r);bad=[x['id']+' 차트 '+x['L'] for x in r if not x['ok']]
        leg=await pg.evaluate("()=>typeof DRILL_CHARTS==='undefined'&&typeof pfChartLetter==='undefined'&&!JSON.stringify(RANGES).includes('pg')")
        if not leg:bad.append('예전 차트 데이터·페이지 번호가 남아 있음')
    print(f'차트 대응 {tot}개 확인');print('FAIL '+str(bad[:10]) if bad else 'OK');srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
