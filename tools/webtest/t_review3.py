# 핸드 복기 저장(내 계정): 게스트는 가입 안내, 가입한 플레이어는 저장·목록·열기·고치기·삭제, 다른 기기에서도 보임, 홈 카드 개수, 남의 기록은 못 읽음, 50개 제한
import asyncio,sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
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
async def frame(pg):
    await pg.evaluate("()=>{reviewClose();MENUTAB='home';menu();document.getElementById('goRv').click()}");await asyncio.sleep(1.2)
    fr=[f for f in pg.frames if f.url.endswith('review/index.html')][0];await fr.wait_for_selector('#hand-review');await asyncio.sleep(.3);return fr
async def main():
    srv=start_server();store['meta/season']={'v':0};ok=True
    def chk(name,cond,info=''):
        nonlocal ok;print('PASS' if cond else 'FAIL',name,info if not cond else '');ok=ok and bool(cond)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        adm=await mkpage(b,{'anon':'a_adm','google':{'uid':'g_owner','email':ADMIN}})
        await adm.click('#admIn');await settle(1);await adm.click('#adGo');await asyncio.sleep(.3)
        await adm.fill('#accin','abcd1');await adm.click('#accf button[type=submit]');await settle()
        # 게스트: 저장 대신 가입 안내
        g=await mkpage(b,{'anon':'u_guest'});fr=await frame(g)
        await fr.evaluate("()=>document.getElementById('hr-ex').click()");await asyncio.sleep(.6)
        await fr.evaluate("()=>document.querySelector('#hr-savebar [data-sv=new]').click()");await asyncio.sleep(.2)
        t=await fr.evaluate("()=>document.getElementById('hr-dosave').textContent+'|'+document.getElementById('hr-sheetmsg').textContent")
        chk('게스트는 가입 안내',('가입' in t) and ('가입한 플레이어만' in t),t)
        try:await fr.evaluate("()=>{setTimeout(()=>document.getElementById('hr-dosave').click(),0)}")
        except Exception:pass
        await asyncio.sleep(.6)
        chk('가입 버튼 → 가입 화면',await g.evaluate("()=>SCREEN")=='join' and not await g.query_selector('#hrov'))
        await submit(g,'abcd1','게스트왕','4321');await settle(1)
        fr=[f for f in g.frames if f.url.endswith('review/index.html')]
        chk('가입 뒤 복기 화면으로 돌아옴',bool(fr) and await g.query_selector('#hrov') is not None)
        if fr:
            fr=fr[0];await asyncio.sleep(.6)
            st=await fr.evaluate("()=>({rv:!document.getElementById('hr-replay').hidden,bar:document.getElementById('hr-savebar').innerText})")
            chk('보던 복기를 다시 불러옴',st['rv'] and '이 복기 저장' in st['bar'],st)
        # 플레이어 가입
        pa=await mkpage(b,{'anon':'u_pa'});await open_join(pa,'new');await submit(pa,'abcd1','올인','1234')
        uid=await pa.evaluate("()=>LB.uid");fr=await frame(pa)
        await fr.evaluate("()=>document.getElementById('hr-ex').click()");await asyncio.sleep(.6)
        await fr.evaluate("()=>document.querySelector('#hr-savebar [data-sv=new]').click()");await asyncio.sleep(.2)
        nm=await fr.evaluate("()=>document.getElementById('hr-name').value")
        chk('이름 자동 채움',nm.startswith(f"{__import__('datetime').date.today().month}/") and 'BTN' in nm and 'vs' in nm,nm)
        await fr.fill('#hr-memo','상대가 자주 3벳해요')
        await fr.evaluate("()=>document.getElementById('hr-dosave').click()");await settle(1)
        d=store.get('hreview/'+uid)
        chk('서버에 저장',bool(d) and len(d['r'])==1 and d['r'][0]['m']=='상대가 자주 3벳해요',d and len(d['r']))
        bar=await fr.evaluate("()=>document.getElementById('hr-savebar').innerText")
        chk('저장됨 표시',('저장됨' in bar) and ('이름·메모 고치기' in bar),bar)
        # 홈 카드
        await pa.evaluate("()=>document.getElementById('hrClose').click()");await settle()
        card=await pa.evaluate("()=>document.getElementById('goRv').innerText")
        chk('홈 카드에 저장 1',('저장 1' in card) and ('최근' in card),card)
        # 다른 기기(같은 닉네임)에서 목록 보고 열기
        pb=await mkpage(b,{'anon':'u_pb'});await open_join(pb,'login');await submit(pb,'abcd1','올인','1234');await settle(1)
        fb=await frame(pb);await fb.evaluate("()=>document.getElementById('hr-tab-my').click()");await asyncio.sleep(1)
        lst=await fb.evaluate("()=>({n:document.querySelectorAll('#hr-mylist [data-open]').length,cnt:document.getElementById('hr-mycnt').textContent,t:document.getElementById('hr-mylist').innerText})")
        chk('다른 기기에서 목록 1개',lst['n']==1 and lst['cnt']=='1',lst)
        await fb.evaluate("()=>document.querySelector('#hr-mylist [data-open]').click()");await asyncio.sleep(.8)
        st=await fb.evaluate("()=>({rv:!document.getElementById('hr-replay').hidden,story:document.getElementById('hr-story').innerText.length,bar:document.getElementById('hr-savebar').innerText})")
        chk('열면 전체 해설과 메모',st['rv'] and st['story']>200 and '상대가 자주 3벳해요' in st['bar'],st)
        # 이름 고치기
        await fb.evaluate("()=>document.querySelector('#hr-savebar [data-sv=upd]').click()");await asyncio.sleep(.2)
        await fb.fill('#hr-name','내가 고친 이름');await fb.evaluate("()=>document.getElementById('hr-dosave').click()");await settle(1)
        d=store.get('hreview/'+uid);chk('이름 고치기(개수 그대로)',len(d['r'])==1 and d['r'][0]['t']=='내가 고친 이름',[x['t'] for x in d['r']])
        # 입력 화면에서 액션 하나 되돌리고 → 바뀐 내용 저장 / 새로 저장
        await fb.evaluate("()=>document.querySelector('#hr-savebar [data-sv=edit]').click()");await asyncio.sleep(.3)
        await fb.evaluate("()=>document.getElementById('hr-undo').click()");await asyncio.sleep(.2)
        await fb.evaluate("()=>{const b=document.querySelector('#hr-recbody [data-act=fold]');b.click()}");await asyncio.sleep(.2)
        await fb.evaluate("()=>document.querySelector('#hr-guide [data-go=result]').click()");await asyncio.sleep(.6)
        bar=await fb.evaluate("()=>document.getElementById('hr-savebar').innerText")
        chk('바꾸면 두 가지 저장 버튼',('바뀐 내용 저장' in bar) and ('새로 저장' in bar),bar)
        await fb.evaluate("()=>document.querySelector('#hr-savebar [data-sv=new]').click()");await asyncio.sleep(.2)
        await fb.evaluate("()=>document.getElementById('hr-dosave').click()");await settle(1)
        d=store.get('hreview/'+uid);chk('새로 저장 → 2개',len(d['r'])==2,len(d['r']))
        # 삭제 (두 번 눌러야)
        await fb.evaluate("()=>document.querySelector('#hr-savebar [data-sv=del]').click()");await asyncio.sleep(.2)
        chk('한 번 누르면 아직 안 지움',len(store['hreview/'+uid]['r'])==2)
        await fb.evaluate("()=>document.querySelector('#hr-savebar [data-sv=del]').click()");await settle(1)
        chk('두 번 누르면 삭제',len(store['hreview/'+uid]['r'])==1 and await fb.evaluate("()=>!document.getElementById('hr-my').hidden"))
        # 50개 제한
        full=[dict(store['hreview/'+uid]['r'][0],id='x%d'%i) for i in range(50)];store['hreview/'+uid]={'r':full,'at':1};await settle()
        fb=await frame(pb);await fb.evaluate("()=>document.getElementById('hr-ex').click()");await asyncio.sleep(.6)
        await fb.evaluate("()=>document.querySelector('#hr-savebar [data-sv=new]').click()");await asyncio.sleep(.2)
        await fb.evaluate("()=>document.getElementById('hr-dosave').click()");await settle(1)
        msg=await fb.evaluate("()=>document.getElementById('hr-sheetmsg').textContent")
        chk('50개면 저장 막고 안내','50개까지' in msg and len(store['hreview/'+uid]['r'])==50,msg)
        # 권한: 다른 플레이어는 못 읽고 못 씀
        u2={'uid':'zz','email':'p'+'0'*32+'@players.allin-iq.app'}
        chk('남의 복기 읽기 거절',not can_read('hreview/'+uid,u2))
        chk('남의 복기 쓰기 거절',not can_write('hreview/'+uid,{'r':[],'at':1},u2))
        chk('51개 쓰기 거절',not can_write('hreview/'+uid,{'r':[{}]*51,'at':1},{'uid':uid,'email':store['names/올인'] and 'x'}) )
        errs=[e for q in (adm,g,pa,pb) for e in q.errs if 'ERR_FAILED' not in e]
        chk('화면 오류 없음',not errs,errs[:3])
    print('OK' if ok else 'FAIL');srv.shutdown();sys.exit(0 if ok else 1)
asyncio.run(main())
