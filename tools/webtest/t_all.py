import asyncio,sys,hashlib
import os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server()
    store['secret/access']={'code':'ABCD1'};salt='aa';store['meta/access']={'h':hashlib.sha256(('hgq-acc:'+salt+':ABCD1').encode()).hexdigest(),'salt':salt}
    store['meta/season']={'v':0}
    R=lambda n,h,d:{'name':n,'season':0,'hands':h,'sum':h*70,'avg':70,'best':1,'dn':d,'dsum':d*80,'davg':80,'dbest':1,'at':1}
    store['scores/a']=R('핸드만',20,0);store['scores/b']=R('둘다5',5,5);store['scores/c']=R('연습4',9,4)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1);await broadcast();await asyncio.sleep(.5)
        for h,d in [(7,0),(5,4),(5,5)]:
            await pg.evaluate(f"()=>{{STATS={{n:{h},sum:{h*60},streak:0,best:0}};DSTATS={{n:{d},sum:{d*90},streak:0,best:0}};menu()}}")
            print(h,d,'->',await pg.evaluate("()=>document.querySelector('.mov').innerText"))
        await pg.evaluate("()=>{LB.tab='all';lbRender()}")
        print('ALL:',(await pg.evaluate("()=>document.getElementById('lbbox').innerText")).replace('\n',' / ')[:420])
        await pg.evaluate("()=>{LB.tab='hand';lbRender()}")
        print('HAND:',(await pg.evaluate("()=>document.querySelector('.lbl').innerText")).replace('\n',' / ')[:200])
        print('errs',[e for e in pg.errs if 'ERR_FAILED' not in e])
        await b.close()
    srv.shutdown()
asyncio.run(main())
