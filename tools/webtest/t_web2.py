import asyncio,json,sys
import os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
S=lambda:{k:(v.get('name'),v.get('hands')) for k,v in store.items() if k.startswith('scores/')}
N=lambda:{k:(v.get('uid'),v.get('gen'),v.get('reset')) for k,v in store.items() if k.startswith('names/')}
async def settle(t=.6):await asyncio.sleep(t);await broadcast();await asyncio.sleep(.4)
async def play(pg,n):
    if await pg.evaluate("()=>SCREEN")!='hand':await pg.evaluate("()=>start(0)");await asyncio.sleep(.2)
    for k in range(400):
        if await pg.evaluate("()=>STATS.n")>=n or await pg.evaluate("()=>SCREEN")!='hand':break
        nx=await pg.query_selector('#next')
        if nx:await nx.click();continue
        bt=await pg.query_selector_all('#panel button[data-k]')
        if not bt:await asyncio.sleep(.1);continue
        await bt[0].click()
    await pg.evaluate("()=>{if(SCREEN==='hand')menu()}")
async def open_join(pg,mode):
    await pg.evaluate("()=>menu()");await pg.click('#go');await asyncio.sleep(.3)
    if mode in('new','login'):await pg.click(f'[data-jm="{mode}"]');await asyncio.sleep(.1)
async def submit(pg,code,name=None,pin=None,pin2=None,temp=None):
    await pg.fill('#jc',code)
    if name is not None:await pg.fill('#jn',name)
    if temp is not None:await pg.fill('#jt',temp)
    if pin is not None:await pg.fill('#jp',pin)
    if await pg.query_selector('#jp2'):await pg.fill('#jp2',pin if pin2 is None else pin2)
    await pg.click('#jgo');await settle(.8)
async def jerr(pg):
    e=await pg.query_selector('#jerr');return (await e.inner_text()) if e and await e.is_visible() else None
async def reload(pg):await pg.reload();await asyncio.sleep(.8);await broadcast();await asyncio.sleep(.5)
async def main():
    srv=start_server()
    async with async_playwright() as p:
        b=await p.chromium.launch()
        adm=await mkpage(b,{'anon':'a_adm','google':{'uid':'g_owner','email':ADMIN}})
        await adm.click('#admIn');await settle(1)
        await adm.click('#adGo');await asyncio.sleep(.3)
        await adm.fill('#accin','abcd1');await adm.click('#accf button[type=submit]');await settle()
        print('1 code set',store.get('secret/access',{}).get('code'))
        # player 1 registers on phone A
        pa=await mkpage(b,{'anon':'u_pa'})
        await open_join(pa,'new');print('2 join tabs',await pa.evaluate("()=>[...document.querySelectorAll('[data-jm]')].map(x=>x.innerText)"))
        await submit(pa,'abcd1','올인','1234','1235');print('3 pin mismatch:',await jerr(pa))
        await submit(pa,'zzzz9','올인','1234');print('4 wrong code:',await jerr(pa))
        await submit(pa,'abcd1','올인','1234');print('5 registered:',await pa.evaluate("()=>[SCREEN,gateState(),MYNAME,LB.uid]"),N(),'acct',list(accounts.values()))
        await play(pa,5);await settle();print('6 score saved',S())
        print('7 menu row:',await pa.evaluate("()=>[!!document.getElementById('rename'),(document.querySelector('#panel .admrow')||{}).innerText]"))
        # player 2 tries the same nickname (different case/spaces)
        pb=await mkpage(b,{'anon':'u_pb'})
        await open_join(pb,'new');await submit(pb,'abcd1','올인','5555');print('8 dup nickname:',await jerr(pb))
        await submit(pb,'abcd1','리버킹','5555');print('9 p2 ok:',await pb.evaluate("()=>[gateState(),MYNAME]"))
        await open_join(pb,'new') if await pb.evaluate("()=>gateState()")!='open' else None
        # same player on phone B (fresh browser) with the wrong then right password
        pc=await mkpage(b,{'anon':'u_pc'})
        await open_join(pc,'login');await submit(pc,'abcd1','없는닉','1234');print('10 unknown nick:',await jerr(pc))
        await submit(pc,'abcd1','올인','9999');print('11 wrong pw:',await jerr(pc))
        await submit(pc,'abcd1','올인','1234');await asyncio.sleep(.5);await broadcast();await asyncio.sleep(.8)
        print('12 phone B as same player:',await pc.evaluate("()=>[LB.uid,MYNAME,gateState(),STATS.n]"))
        await play(pc,8);await settle();print('13 continued on phone B',S())
        # phone A reload sees merged record
        await reload(pa);print('14 phone A after reload',await pa.evaluate("()=>[LB.uid,MYNAME,gateState(),STATS.n]"))
        # bypass attempts from a guest
        pg_=await mkpage(b,{'anon':'u_hack'})
        r=await pg_.evaluate("""async()=>{const o={};
          try{await LB.db.doc('names/올인').set({uid:LB.uid,name:'올인',gen:0,at:1})}catch(e){o.steal=e.code}
          try{await LB.db.doc('members/'+LB.uid).set({code:'ABCD1',name:'올인',at:1})}catch(e){o.member=e.code}
          try{await LB.db.doc('scores/'+LB.uid).set({name:'올인',season:0,hands:1,sum:1,best:0,dn:0,dsum:0,dbest:0})}catch(e){o.score=e.code}
          try{await LB.db.doc('secret/rs_올인').get()}catch(e){o.rs=e.code}
          return o}""");print('15 guest bypass:',r)
        # registered player 2 tries to write as player 1
        r=await pb.evaluate("""async()=>{const o={};
          try{await LB.db.doc('members/'+LB.uid).set({code:'ABCD1',name:'올인',at:1})}catch(e){o.member=e.code}
          try{await LB.db.doc('scores/'+LB.uid).set({name:'올인',season:LB.season,hands:1,sum:1,best:0,dn:0,dsum:0,dbest:0,at:1})}catch(e){o.score=e.code}
          return o}""");print('16 p2 impersonation:',r)
        # code change → recode only
        await adm.evaluate("()=>adminScreen()");await asyncio.sleep(.3)
        await adm.fill('#accin','newcode9');await adm.click('#accf button[type=submit]');await settle()
        print('17 after code change p1(B):',await pc.evaluate("()=>[SCREEN,gateState()]"),await pc.evaluate("()=>!!document.getElementById('jn')"))
        if await pc.evaluate("()=>SCREEN")!='join':await pc.click('#go');await asyncio.sleep(.3)
        await submit(pc,'newcode9');print('18 recode ok:',await pc.evaluate("()=>[gateState(),MYNAME]"))
        # admin reset password for 올인
        await adm.evaluate("()=>adminScreen()");await asyncio.sleep(.4)
        btn=await adm.query_selector('[data-rst="올인"]');print('19 reset button',bool(btn))
        await btn.click();await settle()
        temp=store.get('secret/rs_올인',{}).get('t');print('20 temp shown:',temp and temp in await adm.evaluate("()=>document.getElementById('adPl').innerText"),N())
        pd=await mkpage(b,{'anon':'u_pd'})
        await open_join(pd,'login');await submit(pd,'newcode9','올인','1234');print('21 login during reset:',await pd.evaluate("()=>J_mode=document.getElementById('jt')?'reset form':'no'"),await jerr(pd))
        await submit(pd,'newcode9','올인','4321',temp='000000');print('22 wrong temp:',await jerr(pd),'accounts',len(accounts))
        await submit(pd,'newcode9','올인','4321',temp=temp);await asyncio.sleep(.5);await broadcast();await asyncio.sleep(.8)
        print('23 claimed:',await pd.evaluate("()=>[LB.uid,MYNAME,gateState(),STATS.n]"),S(),N())
        # old phone with old account: writes now rejected → back to join
        await play(pc,9);await settle()
        print('24 old session after reset:',await pc.evaluate("()=>[SCREEN,gateState(),LB.writeFail]"),S())
        # logout on shared phone
        await pb.evaluate("()=>menu()");await pb.click('#plOut');await asyncio.sleep(1);await broadcast();await asyncio.sleep(.5)
        print('25 after logout:',await pb.evaluate("()=>[LB.uid,MYNAME,gateState(),STATS.n]"))
        print('denied',denied[-6:])
        for q in pages:
            if q.errs:print('ERR',q.errs[:3])
        await b.close()
    srv.shutdown()
asyncio.run(main())
