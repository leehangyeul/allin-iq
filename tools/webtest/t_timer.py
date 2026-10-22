import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server()
    store['meta/season']={'v':0}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1);await broadcast();await asyncio.sleep(.5)
        # hand quiz
        await pg.evaluate("()=>start(0)");await asyncio.sleep(.8)
        t0=await pg.evaluate("()=>document.querySelector('#qtm b').textContent")
        print('hand timer shown, start',t0)
        await asyncio.sleep(3);print('after 3s+',await pg.evaluate("()=>document.querySelector('#qtm b').textContent"))
        await pg.screenshot(path='/tmp/t_timer_hand.png')
        n0=await pg.evaluate("()=>STATS.n")
        # answer before timeout must stop timer: click first button on a new hand later; now wait for timeout
        await asyncio.sleep(24)
        r=await pg.evaluate("()=>({n:STATS.n,d:G.dec.map(x=>[x.k,x.to]),txt:document.body.innerText.includes('시간 초과')})")
        print('after timeout',n0,'->',r)
        await pg.screenshot(path='/tmp/t_timer_res.png')
        # quick answer path: next hand, answer at once, nothing should fire later
        await pg.evaluate("()=>start(0)");await asyncio.sleep(.8)
        await pg.evaluate("()=>document.querySelector('button[data-k]').click()");await asyncio.sleep(.3)
        print('timer cleared after click:',await pg.evaluate("()=>QT===null"))
        # drill
        await pg.evaluate("()=>drillStart()");await asyncio.sleep(.5)
        print('drill timer',await pg.evaluate("()=>document.querySelector('#qtm b').textContent"))
        d0=await pg.evaluate("()=>DSTATS.n")
        await asyncio.sleep(21.5)
        print('drill after timeout',d0,'->',await pg.evaluate("()=>({n:DSTATS.n,pick:DS.pick})"))
        print('errs',[e for e in pg.errs if 'ERR_FAILED' not in e])
        await b.close()
    srv.shutdown()
asyncio.run(main())
