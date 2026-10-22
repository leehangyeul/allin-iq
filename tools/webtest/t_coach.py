import asyncio,sys,os,json,random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
POSG=["UTG","UTG+1","UTG+2","LJ","HJ","CO","BTN","SB","BB"]
def mk(n,g,weak):
    random.seed(n+(1 if g=="h" else 2));out=[]
    for i in range(1,n+1):
        p=random.choice(POSG);st=random.choice([100,40,25,10]) if g=="h" else random.choice([75,40,25,15,10])
        grp={"UTG":"EP","UTG+1":"EP","UTG+2":"EP","LJ":"MP","HJ":"MP","CO":"LP","BTN":"LP","SB":"BL","BB":"BL"}[p]
        base=80
        if grp=="EP":base=55           # weak in both games
        if grp=="LP":base=90           # strong in both games
        if st<20:base-=5
        sc=max(0,min(100,int(random.gauss(base,10))))
        out.append({"i":i,"p":p,"st":st,"s":0,"sc":sc,"pf":random.choice([0,100,20,80]),"fo":random.choice([0,1]),"to":0})
    return out
async def main():
    srv=start_server();store['meta/season']={'v':0}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1);await broadcast();await asyncio.sleep(.5)
        # locked state
        await pg.evaluate("()=>{CL={hn:12,dn:50,h:[],d:[]};menu()}")
        print('tile locked:',(await pg.evaluate("()=>document.getElementById('go3').innerText")).replace('\n',' | '))
        await pg.evaluate("()=>coachScreen()");await asyncio.sleep(.3)
        print('lock screen:',(await pg.evaluate("()=>document.getElementById('panel').innerText")).replace('\n',' | ')[:160])
        # ready state with fake records (EP weak, LP strong in both games)
        h=mk(150,"h",1);d=mk(150,"d",1)
        await pg.evaluate("(x)=>{CL={hn:150,dn:150,h:x[0],d:x[1]};menu()}",[h,d])
        print('tile ready:',(await pg.evaluate("()=>document.getElementById('go3').innerText")).replace('\n',' | '))
        await pg.evaluate("()=>coachScreen()");await asyncio.sleep(.3)
        print((await pg.evaluate("()=>document.getElementById('panel').innerText")).replace('\n',' | ')[:900])
        await pg.set_viewport_size({'width':390,'height':844})
        await pg.screenshot(path='/tmp/t_coach1.png',full_page=True)
        await pg.evaluate("()=>{MYNAME='테스터';lsSet('hgq-name','테스터')}")
        # practice button -> drill filtered to EP
        await pg.evaluate("()=>document.querySelector('[data-cf]').click()");await asyncio.sleep(.8)
        r=await pg.evaluate("()=>({s:SCREEN,pos:DS&&DS.sp.pos,f:DFILT})")
        print('focus drill:',r)
        poss=set()
        for _ in range(25):
            poss.add(await pg.evaluate("()=>{drillNext();return DS.sp.pos}"))
        print('focused positions seen:',sorted(poss))
        # recording hooks: answer a drill and a hand
        n0=await pg.evaluate("()=>CL.dn");await pg.evaluate("()=>{DFILT=null;drillNext();drillAnswer(DS.sp.kind==='chart'?'f':'f')}")
        print('drill record added:',await pg.evaluate("()=>CL.dn")-n0, await pg.evaluate("()=>JSON.stringify(CL.d[CL.d.length-1])"))
        await pg.evaluate("()=>start(0)");await asyncio.sleep(.8)
        hn0=await pg.evaluate("()=>CL.hn");await pg.evaluate("()=>{const b=document.querySelector('button[data-k=fold]')||document.querySelector('button[data-k]');b.click()}");await asyncio.sleep(.5)
        print('hand record added:',await pg.evaluate("()=>CL.hn")-hn0, await pg.evaluate("()=>JSON.stringify(CL.h[CL.h.length-1])"))
        await pg.evaluate("()=>{clearLocal()}");print('cleared:',await pg.evaluate("()=>[CL.hn,CL.dn,CL.h.length,CL.d.length]"))
        print('errs',[e for e in pg.errs if 'ERR_FAILED' not in e]);await b.close()
    srv.shutdown()
asyncio.run(main())
