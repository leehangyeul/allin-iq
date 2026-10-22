import asyncio,sys,os,json,random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1)
        # A. combined average formula
        for hn,hs,dn,ds in [(10,600,400,36000),(5,450,5,250),(4,400,300,20000),(200,12000,5,500)]:
            r=await pg.evaluate("([a,b,c,d])=>{STATS={n:a,sum:b,streak:0,best:0};DSTATS={n:c,sum:d,streak:0,best:0};const m=myCard();const lp=lbPick({hands:a,sum:b,avg:a?Math.round(b/a*10)/10:0,dn:c,dsum:d,davg:c?Math.round(d/c*10)/10:0,best:0,dbest:0},'all');return {ha:m.ha,da:m.da,ta:m.ta,ready:m.ready,lb:lp.avg}}",[hn,hs,dn,ds])
            exp=(hs+ds)/(hn+dn)
            print(f"hand {hn}x{hs/hn:.0f} drill {dn}x{ds/dn:.0f} -> menu {r} expected {exp:.1f} equal-weight {(hs/hn+ds/dn)/2:.1f}")
        # B. play real hands, compare displayed score and running average
        await pg.evaluate("()=>{clearLocal();MYNAME='테스터';lsSet('hgq-name','테스터')}")
        tots=[]
        for k in range(6):
            await pg.evaluate("()=>start(0)");await asyncio.sleep(.6)
            for _ in range(40):
                ok=await pg.evaluate("()=>{const b=document.querySelector('#panel button[data-k]');if(!b)return false;b.click();return true}")
                if not ok:break
                await asyncio.sleep(.25)
            s=await pg.evaluate("()=>({n:STATS.n,sum:STATS.sum,big:(document.querySelector('.scr .big')||{}).innerText,row:(document.querySelector('.statrow')||{}).innerText})")
            tots.append(s)
        prev=0
        for i,s in enumerate(tots):
            d=s['sum']-prev;prev=s['sum']
            print(f"hand{i+1}: n={s['n']} added={d} shown={(s['big'] or '').split('/')[0].strip()} avgrow={(s['row'] or '').replace(chr(10),' ')[:60]} exact={s['sum']/max(1,s['n']):.1f}")
        # C. drills
        d0=await pg.evaluate("()=>({n:DSTATS.n,sum:DSTATS.sum})");prev=d0['sum']
        for k in range(8):
            await pg.evaluate("()=>{drillNext();}");await asyncio.sleep(.2)
            await pg.evaluate("()=>drillAnswer(['f','r','c','j'].find(x=>true))")
            await asyncio.sleep(.2)
            s=await pg.evaluate("()=>({n:DSTATS.n,sum:DSTATS.sum,txt:(document.querySelector('.sdn')||{}).innerText,row:(document.querySelector('.statrow')||{}).innerText})")
            print(f"drill{k+1}: n={s['n']} added={s['sum']-prev} shown='{(s['txt'] or '')[:28]}' row={(s['row'] or '').replace(chr(10),' ')[:50]} exact={s['sum']/s['n']:.1f}");prev=s['sum']
        print('errs',[e for e in pg.errs if 'ERR_FAILED' not in e]);await b.close()
    srv.shutdown()
asyncio.run(main())
