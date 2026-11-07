# 핸드 마크(11/6): 결과 화면 별 → 태그·메모 저장, 더보기 → 마크한 핸드 목록·태그 거르기·다시 보기, 다시 풀기는 점수 제외,
# 내 계정(hmark/{uid}) 저장 → 다른 기기에서도 보임, 남의 기록은 못 읽음, 마크 해제. 평균 스택·SPR 줄 표시.
import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
SHOT='/tmp/claude-0/-home-claude/2d74400d-a8fa-525d-a7f9-6321452de973/scratchpad/fb/'
async def settle(t=.6):await asyncio.sleep(t);await broadcast();await asyncio.sleep(.5)
async def open_join(pg,mode):
    await pg.evaluate("()=>{MENUTAB='home';menu()}");await pg.click('#go');await asyncio.sleep(.3)
    if mode in('new','login'):await pg.click(f'[data-jm="{mode}"]');await asyncio.sleep(.1)
async def submit(pg,code,name=None,pin=None):
    await pg.fill('#jc',code)
    if name is not None:await pg.fill('#jn',name)
    if pin is not None:await pg.fill('#jp',pin)
    if await pg.query_selector('#jp2'):await pg.fill('#jp2',pin)
    await pg.click('#jgo');await settle(.8)
async def play_to_result(pg,idx):
    await pg.evaluate("(i)=>{qTimerStop();start(0);order[hi]=LEVELS[0].hands[i];newHand()}",idx);await asyncio.sleep(.2)
    for _ in range(20):
        k=await pg.evaluate("()=>{const c=G.sub||G.cur;const b=document.querySelector('#panel button[data-k]');if(!b)return null;const mo=mergedOF(c);return bestOf(mo.o,mo.f)}")
        if not k:break
        await pg.evaluate("(k)=>document.querySelector('#panel button[data-k=\"'+k+'\"]').click()",k);await asyncio.sleep(.05)
async def wait_eq(pg,expr,val,t=6):
    for _ in range(int(t/.3)):
        await broadcast()
        if await pg.evaluate(expr)==val:return True
        await asyncio.sleep(.3)
    return False
async def main():
    srv=start_server();store['meta/season']={'v':0};ok=True
    def chk(name,cond,info=''):
        nonlocal ok;print('PASS' if cond else 'FAIL',name,info);ok=ok and bool(cond)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        adm=await mkpage(b,{'anon':'a_adm','google':{'uid':'g_owner','email':ADMIN}})
        await adm.click('#admIn');await settle(1);await adm.click('#adGo');await asyncio.sleep(.3)
        await adm.fill('#accin','abcd1');await adm.click('#accf button[type=submit]');await settle()
        pa=await mkpage(b,{'anon':'u_pa'});await open_join(pa,'new');await submit(pa,'abcd1','마커','1234')
        uid=await pa.evaluate("()=>LB.uid");chk('가입',bool(uid))
        await pa.set_viewport_size({'width':390,'height':844})
        # 평균 스택·SPR 줄: 프리플랍은 SPR '-', 플랍부터 숫자
        idx=await pa.evaluate("()=>LEVELS[0].hands.findIndex(h=>!h.multi&&h.s.length>=3&&(h.d||100)===100)")
        await pa.evaluate("(i)=>{qTimerStop();start(0);order[hi]=LEVELS[0].hands[i];newHand()}",idx);await asyncio.sleep(.3)
        t=await pa.evaluate("()=>document.querySelector('.sstrip').innerText")
        chk('평균 스택 줄(프리플랍)', '평균 스택' in t and '100BB' in t and 'SPR' in t and '평균 대비' in t,t.replace('\n',' '))
        k=await pa.evaluate("()=>{const c=G.cur;const mo=mergedOF(c);return bestOf(mo.o,mo.f)}")
        await pa.evaluate("(k)=>document.querySelector('#panel button[data-k=\"'+k+'\"]').click()",k);await asyncio.sleep(1.2)
        t2=await pa.evaluate("()=>(document.querySelector('.sstrip')||{}).innerText||''")
        spr=await pa.evaluate("()=>{const e=[...document.querySelectorAll('.sstrip>div')].pop();return e?e.querySelector('b').innerText:''}")
        chk('플랍 SPR 숫자',spr.replace('.','').isdigit(),spr)
        await pa.screenshot(path=SHOT+'w_strip.png')
        ov=await pa.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
        await pa.set_viewport_size({'width':320,'height':700});await asyncio.sleep(.2)
        ov2=await pa.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
        chk('가로 넘침 없음(390·320)',ov<=0 and ov2<=0,(ov,ov2))
        await pa.set_viewport_size({'width':390,'height':844})
        # 결과 화면에서 마크
        await play_to_result(pa,idx);n0=await pa.evaluate("()=>STATS.n")
        chk('결과 화면에 마크 버튼',bool(await pa.query_selector('#mkb')))
        await pa.click('#mkb');await asyncio.sleep(.2)
        await pa.click('.mktag[data-t="헷갈림"]');await pa.click('.mktag[data-t="쿨러"]');await pa.fill('#mkmemo','페어 보드 리버 올인 맞나?')
        await pa.screenshot(path=SHOT+'w_sheet.png')
        await pa.click('#mkok');await settle(1)
        L=await pa.evaluate("()=>MK.list.map(x=>({tags:x.tags,memo:x.memo,d:x.d.length,tot:x.tot}))")
        chk('마크 저장(태그·메모)',len(L)==1 and L[0]['tags']==['헷갈림','쿨러'] and L[0]['memo'].startswith('페어'),L)
        chk('버튼이 마크됨으로',await pa.evaluate("()=>document.getElementById('mkb').classList.contains('on')"))
        for _ in range(15):
            if store.get('hmark/'+uid):break
            await asyncio.sleep(.3)
        d=store.get('hmark/'+uid);chk('내 계정에 저장',bool(d) and len(d.get('m',[]))==1,d and len(d.get('m',[])))
        # 두 번째 마크(태그 없음)
        idx2=await pa.evaluate("()=>LEVELS[0].hands.findIndex(h=>h.s.length===1)")
        await play_to_result(pa,idx2);await pa.click('#mkb');await asyncio.sleep(.2);await pa.click('#mkok');await settle(1)
        # 목록·거르기
        await pa.evaluate("()=>{MENUTAB='more';menu()}");await asyncio.sleep(.2)
        chk('더보기에 마크한 핸드 2',(await pa.evaluate("()=>document.querySelector('#mkGo .mkn').innerText")).strip()=='2')
        await pa.click('#mkGo');await asyncio.sleep(.3)
        chk('목록 2개',await pa.evaluate("()=>document.querySelectorAll('.mki').length")==2)
        await pa.screenshot(path=SHOT+'w_list.png')
        await pa.click('.mkf button[data-f="쿨러"]');await asyncio.sleep(.2)
        chk('태그로 거르기',await pa.evaluate("()=>document.querySelectorAll('.mki').length")==1)
        await pa.click('.mki');await asyncio.sleep(.3)
        rows=await pa.evaluate("()=>document.querySelectorAll('.mkr').length")
        chk('다시 보기 스트리트 줄',rows>=2,rows)
        await pa.click('.mkr');await asyncio.sleep(.1)
        chk('줄을 누르면 해설',bool(await pa.query_selector('.mkn2')))
        await pa.screenshot(path=SHOT+'w_detail.png',full_page=True)
        nan=await pa.evaluate("()=>/NaN|undefined|\\[object/.test(document.getElementById('panel').innerText)")
        chk('NaN 없음',not nan)
        # 다시 풀기: 점수 제외
        n1=await pa.evaluate("()=>STATS.n");await pa.click('#mkre');await asyncio.sleep(.3)
        chk('다시 풀기 표시',(await pa.evaluate("()=>document.getElementById('top').innerText")).find('다시 풀기')>=0)
        for _ in range(20):
            kk=await pa.evaluate("()=>{const c=G.sub||G.cur;if(!document.querySelector('#panel button[data-k]'))return null;const mo=mergedOF(c);return bestOf(mo.o,mo.f)}")
            if not kk:break
            await pa.evaluate("(k)=>document.querySelector('#panel button[data-k=\"'+k+'\"]').click()",kk)
        chk('다시 풀기는 점수에 안 들어감',await pa.evaluate("()=>STATS.n")==n1)
        await pa.click('#next');await asyncio.sleep(.3)
        chk('다음 핸드는 정상 출제',await pa.evaluate("()=>!PRACTICE&&order.length>1"))
        # 다른 기기에서 보임
        pc=await mkpage(b,{'anon':'u_pc'});await open_join(pc,'login');await submit(pc,'abcd1','마커','1234');await settle(1.5)
        chk('다른 기기에서도 2개',await wait_eq(pc,"()=>MK.list.length",2),await pc.evaluate("()=>MK.list.length"))
        # 남은 못 읽음
        pd=await mkpage(b,{'anon':'u_pd'});await open_join(pd,'new');await submit(pd,'abcd1','남','5555')
        r=await pd.evaluate("""async(u)=>{const o={};try{await LB.db.doc('hmark/'+u).get()}catch(e){o.read=e.code}try{await LB.db.doc('hmark/'+u).set({m:[],at:1})}catch(e){o.write=e.code}return o}""",uid)
        chk('남의 마크 읽기·쓰기 거절',r.get('read') and r.get('write'),r)
        # 마크 해제 → 다른 기기 반영
        await pa.evaluate("()=>{MENUTAB='more';menu()}");await pa.click('#mkGo');await asyncio.sleep(.2);await pa.click('.mki');await asyncio.sleep(.2);await pa.click('#mkoff');await settle(1.2)
        chk('해제 후 1개(두 기기)',await wait_eq(pa,"()=>MK.list.length",1) and await wait_eq(pc,"()=>MK.list.length",1),(await pa.evaluate("()=>MK.list.length"),await pc.evaluate("()=>MK.list.length")))
        errs=[e for g in (pa,pc,pd) for e in g.errs if 'ERR_FAILED' not in e];chk('콘솔 오류 없음',not errs,errs[:3])
    print('결과:','통과' if ok else '실패');srv.shutdown();sys.exit(0 if ok else 1)
asyncio.run(main())
