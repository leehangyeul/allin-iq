import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1);await broadcast();await asyncio.sleep(.5)
        r=await pg.evaluate("""()=>{
          const sn=LB.season;
          LB.rows=[{id:'u1',name:'랭커',season:sn,hands:20,sum:1600,avg:80,best:3,dn:20,dsum:1400,davg:70,dbest:2},
                   {id:'u2',name:'측정중A',season:sn,hands:3,sum:200,avg:66.7,best:1,dn:0,dsum:0,davg:0,dbest:0},
                   {id:'u3',name:'측정중B',season:sn,hands:8,sum:500,avg:62.5,best:1,dn:2,dsum:100,davg:50,dbest:0}];
          const out={};
          for(const t of ['all','hand','drill']){LB.tab=t;
            const pl=lbHTML(),ad=lbHTML(true);
            out[t]={playerSeesWaiting:/측정중A|측정중B/.test(pl),playerSeesRanker:/랭커/.test(pl),adminSeesWaiting:/측정중A/.test(ad)&&/측정중B/.test(ad)}}
          LB.tab='all';return out}""")
        print(r);print('errs',[e for e in pg.errs if 'ERR_FAILED' not in e]);await b.close()
    srv.shutdown()
asyncio.run(main())
