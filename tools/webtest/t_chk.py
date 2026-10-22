import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1)
        r=await pg.evaluate("""()=>{const bad=[];let n=0,multi=0;
          LEVELS.forEach((L,li)=>L.hands.forEach((h,hi)=>{n++;if(h.multi)multi++;
            const id=`L${li}#${hi} ${h.me} ${h.hand.join('')}${h.multi?' (multi)':''}`;
            const fb=fullBoard(h);const all=[...h.hand,...(h.vh||[]),...(h.vh2||[]),...fb];
            const dup=all.filter((c,i)=>all.indexOf(c)!==i);if(dup.length)bad.push(id+' 카드 중복 '+dup);
            let want=0;h.s.forEach(st=>{want+=st.b.length});if(fb.length!==want)bad.push(id+` 보드 ${fb.length}장 vs 스트리트 합 ${want}`);
            h.s.forEach((st,i)=>{const sum=Object.values(st.f).reduce((a,x)=>a+x,0);if(sum!==100)bad.push(id+` s${i} 빈도합 ${sum}`)});
            if(h.multi&&(!h.vh||!h.vh2))bad.push(id+' 상대 카드 누락');
          }));return {n,multi,bad}}""")
        print(r['n'],'hands',r['multi'],'multi');print('\n'.join(r['bad']) or 'no data errors')
        print('errs',[e for e in pg.errs if 'ERR_FAILED' not in e]);await b.close()
    srv.shutdown()
asyncio.run(main())
