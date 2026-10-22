import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1)
        await pg.set_viewport_size({'width':390,'height':844})
        await pg.evaluate("()=>{start(0);const h=LEVELS[0].hands.find(h=>h.multi&&h.hand.join('')==='J♠J♥');order[hi]=h;newHand()}");await asyncio.sleep(.5)
        for key in ['raise','raise','b75']:
            ok=await pg.evaluate("(k)=>{const b=document.querySelector('#panel button[data-k=\"'+k+'\"]');if(!b)return [false,[...document.querySelectorAll('#panel button[data-k]')].map(x=>x.dataset.k)];b.click();return [true]}",key)
            print(key,ok);await asyncio.sleep(.5)
        print(await pg.evaluate("()=>({ended:G.ended,dec:G.dec.length,scr:(document.querySelector('.scr .big')||{}).innerText,dlv:(document.querySelector('.dlv')||{}).innerText,runl:(document.querySelector('.runl')||{}).innerText,runCards:document.querySelectorAll('.bb .pc.run').length,res:(document.querySelector('.sdn')||{}).innerText})"))
        await pg.screenshot(path='/tmp/t_jj.png');print('errs',[e for e in pg.errs if 'ERR_FAILED' not in e]);await b.close()
    srv.shutdown()
asyncio.run(main())
