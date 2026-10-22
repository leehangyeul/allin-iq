# 코치 기록 서버 저장·합치기: 두 대/세 대 기기 합치기, 중복 없음, 권한, 초기화
import asyncio,sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def settle(t=.6):await asyncio.sleep(t);await broadcast();await asyncio.sleep(.5)
async def open_join(pg,mode):
    await pg.evaluate("()=>menu()");await pg.click('#go');await asyncio.sleep(.3)
    if mode in('new','login'):await pg.click(f'[data-jm="{mode}"]');await asyncio.sleep(.1)
async def submit(pg,code,name=None,pin=None,temp=None):
    await pg.fill('#jc',code)
    if temp is not None:await pg.fill('#jt',temp)
    if name is not None:await pg.fill('#jn',name)
    if pin is not None:await pg.fill('#jp',pin)
    if await pg.query_selector('#jp2'):await pg.fill('#jp2',pin)
    await pg.click('#jgo');await settle(.8)
SEED="""(a)=>{const [n,legacy]=a;CL={hn:n,dn:n,h:[],d:[]};
  for(let i=1;i<=n;i++){CL.h.push({i,p:'BTN',st:40,s:0,sc:70,pf:50,fo:0,to:0});CL.h.push({i,p:'BTN',st:40,s:1,sc:60,pf:null,fo:0,to:0});
    CL.d.push({i,p:'CO',st:25,s:0,sc:80,pf:40,fo:1,to:0})}
  coachSave()}"""
STATE="()=>({hn:CL.hn,dn:CL.dn,hu:new Set(CL.h.map(r=>r.u)).size,du:new Set(CL.d.map(r=>r.u)).size,nou:CL.h.concat(CL.d).filter(r=>!r.u).length,lastI:CL.h.length?CL.h[CL.h.length-1].i:0})"
async def main():
    srv=start_server();store['meta/season']={'v':0}
    ok=True
    def chk(name,cond,info=''):
        nonlocal ok;print('PASS' if cond else 'FAIL',name,info);ok=ok and bool(cond)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        adm=await mkpage(b,{'anon':'a_adm','google':{'uid':'g_owner','email':ADMIN}})
        await adm.click('#admIn');await settle(1);await adm.click('#adGo');await asyncio.sleep(.3)
        await adm.fill('#accin','abcd1');await adm.click('#accf button[type=submit]');await settle()
        pa=await mkpage(b,{'anon':'u_pa'});await open_join(pa,'new');await submit(pa,'abcd1','올인','1234')
        uid=await pa.evaluate("()=>LB.uid");chk('가입',bool(uid),uid)
        # A: 기존(번호 없는) 기록 60핸드/55연습 → 서버로
        await pa.evaluate(SEED,[60,1]);await pa.evaluate("()=>coachPull()");await asyncio.sleep(2.2);await settle()
        d=store.get('coach/'+uid);chk('서버에 저장',bool(d) and d['hn']==60 and d['dn']==60,(d or {}).get('hn'))
        sa=await pa.evaluate(STATE);chk('번호 부여, 중복 없음',sa['nou']==0 and sa['hu']==60 and sa['du']==60,sa)
        # C: 새 기기에서 이어하기 → 서버 기록을 그대로 받음
        pc=await mkpage(b,{'anon':'u_pc'})
        await open_join(pc,'login');await submit(pc,'abcd1','올인','1234');await settle(1.5);await asyncio.sleep(1)
        sc=await pc.evaluate(STATE);chk('새 기기는 서버 기록을 받음(60)',sc['hn']==60 and sc['dn']==60 and sc['hu']==60,sc)
        # 같은 시각에 A와 C가 각자 번호 없는 옛 기록을 더 가지고 있는 경우(합치면 60+30+25)
        await pa.evaluate("()=>{const add=25;for(let k=1;k<=add;k++){CL.h.push({i:CL.hn+k,p:'UTG',st:40,s:0,sc:50,pf:60,fo:1,to:0});CL.d.push({i:CL.dn+k,p:'UTG',st:15,s:0,sc:40,pf:70,fo:0,to:0})}CL.hn+=add;CL.dn+=add;coachSave();coachPull()}")
        await pc.evaluate("()=>{const add=30;for(let k=1;k<=add;k++){CL.h.push({i:CL.hn+k,p:'SB',st:25,s:0,sc:90,pf:20,fo:0,to:0});CL.d.push({i:CL.dn+k,p:'SB',st:10,s:0,sc:95,pf:10,fo:0,to:0})}CL.hn+=add;CL.dn+=add;coachSave();coachPull()}")
        await asyncio.sleep(2.5);await settle(1);await asyncio.sleep(2.5);await settle(1.2)
        sa=await pa.evaluate(STATE);sc=await pc.evaluate(STATE)
        chk('두 기기 합산 115(60+25+30), 중복 없음',sa['hn']==115 and sc['hn']==115 and sa['hu']==115 and sa['dn']==115 and sc['du']==115,(sa,sc))
        chk('번호가 시간순으로 다시 매겨짐',sa['lastI']==115 and sc['lastI']==115)
        d=store.get('coach/'+uid);chk('서버 값 115',d and d['hn']==115 and d['dn']==115,(d or {}).get('hn'))
        # 실제 핸드 1판 + 연습 1문제를 C에서 → A에 반영
        await pc.evaluate("()=>{start(0)}");await asyncio.sleep(.5)
        for _ in range(30):
            ok2=await pc.evaluate("()=>{const x=document.querySelector('#panel button[data-k]');if(!x)return false;x.click();return true}")
            if not ok2:break
            await asyncio.sleep(.2)
        await pc.evaluate("()=>{menu();drillNext();drillAnswer('f')}");await asyncio.sleep(2.5);await settle(1.2)
        await asyncio.sleep(2.5);await settle(1.2)
        n=await pc.evaluate('()=>STATS.n')
        sc=await pc.evaluate(STATE);sa=await pa.evaluate(STATE)
        chk('C에서 푼 핸드·연습이 A에도 그대로 반영',sc['hn']==115+n and sa['hn']==115+n and sa['dn']==116 and sa['hu']==115+n and sc['hu']==115+n,(sc,sa))
        # 권한: 다른 플레이어는 읽기·쓰기 불가
        pd=await mkpage(b,{'anon':'u_pd'});await open_join(pd,'new');await submit(pd,'abcd1','리버킹','5555')
        r=await pd.evaluate("""async(u)=>{const o={};try{await LB.db.doc('coach/'+u).get()}catch(e){o.read=e.code}
          try{await LB.db.doc('coach/'+u).set({season:0,hn:1,dn:0,h:[],d:[],at:1})}catch(e){o.write=e.code}return o}""",uid)
        chk('다른 플레이어 읽기·쓰기 거절',r.get('read')=='invalid_argument' and r.get('write')=='invalid_argument',r)
        r=await pd.evaluate("""async()=>{const o={};try{await LB.db.doc('coach/'+LB.uid).set({season:LB.season,hn:1,dn:0,h:[],d:[],at:1,extra:1})}catch(e){o.extra=e.code}return o}""")
        chk('허용되지 않은 필드 거절',r.get('extra')=='invalid_argument',r)
        # 관리자 초기화(기록 삭제): 모든 기기가 0부터, 서버 옛 기록 되살아나지 않음
        await adm.evaluate("async(u)=>{await LB.db.doc('meta/kick').set({ids:{...LB.kicks,[u]:Date.now()}});await LB.db.doc('scores/'+u).delete();await LB.db.doc('coach/'+u).delete()}",uid)
        await settle(1.5);await asyncio.sleep(1.5);await settle(1)
        sa=await pa.evaluate(STATE);sc=await pc.evaluate(STATE)
        chk('초기화 후 두 기기 모두 0',sa['hn']==0 and sc['hn']==0 and sa['dn']==0,(sa,sc))
        chk('서버에서도 삭제',('coach/'+uid) not in store)
        await pa.evaluate("()=>{menu();drillNext();drillAnswer('f')}");await asyncio.sleep(2.5);await settle(1.2)
        sc=await pc.evaluate(STATE);d=store.get('coach/'+uid)
        chk('초기화 뒤 새 기록은 1부터, 다른 기기에도',sc['dn']==1 and d and d['dn']==1,sc)
        # 비밀번호 초기화 → 새 계정으로 이어받으면 코치 기록도 새 계정으로 이동
        await adm.evaluate("()=>adminScreen()");await asyncio.sleep(.4)
        btn=await adm.query_selector('[data-rst="올인"]');await btn.click();await settle()
        temp=store.get('secret/rs_올인',{}).get('t')
        pe=await mkpage(b,{'anon':'u_pe'});await open_join(pe,'login');await submit(pe,'abcd1','올인','1234');await submit(pe,'abcd1','올인','4321',temp=temp)
        await asyncio.sleep(.8);await broadcast();await asyncio.sleep(1.2)
        nu=await pe.evaluate("()=>LB.uid");d=store.get('coach/'+nu)
        chk('초기화 후 새 계정으로 코치 기록 이동',nu!=uid and d and d['dn']==1 and ('coach/'+uid) not in store,(nu,(d or {}).get('dn')))
        sn=await pe.evaluate(STATE);chk('새 계정 기기에서도 보임',sn['dn']==1,sn)
        errs=[e for q in pages for e in q.errs if 'ERR_FAILED' not in e]
        chk('콘솔 오류 없음',not errs,errs[:3])
        await b.close()
    srv.shutdown();print('\n결과:','통과' if ok else '실패');sys.exit(0 if ok else 1)
asyncio.run(main())
