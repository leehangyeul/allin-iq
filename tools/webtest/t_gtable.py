# GTO 홀덤 테이블(11/9): 홈 카드 → 테이블 화면(앱 안), 내 계정 스택 이어가기(gtable/{uid}), 힌트 없음, 빌런 성향 저장,
# 탈락 화면·다시 받기(매일 0시), 관리자 설정(meta/gtable)·스택 되돌리기, 남의 기록 못 읽음, 잘못된 값 거부, 금지 표현 없음.
import asyncio,sys,os,time,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
SHOT='/tmp/claude-0/-home-claude/2d74400d-a8fa-525d-a7f9-6321452de973/scratchpad/gtt2/'
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
def frame(pg):
    for f in pg.frames:
        if '/table/' in f.url:return f
    return None
async def open_table(pg):
    await pg.evaluate("()=>{gtClose();MENUTAB='home';menu()}");await asyncio.sleep(.2)
    await pg.click('#goGt');await asyncio.sleep(.5)
    for _ in range(40):
        f=frame(pg)
        if f:
            try:
                if await f.evaluate("()=>!!(document.querySelector('#b-start:not([hidden])')||document.querySelector('#bz-quiz')||document.querySelector('#g-go'))"):return f
            except Exception:pass
        await asyncio.sleep(.25)
    return frame(pg)
async def play(f,n,t=240):
    ends=0;acts=0;bad=[];t0=time.time()
    while ends<n and time.time()-t0<t:
        if await f.evaluate("()=>!!document.querySelector('#bz-quiz')"):bad.append('BUST');break
        if await f.evaluate("()=>{const b=document.querySelector('#sh-next');return !!(b&&b.offsetParent)}"):
            tx=await f.evaluate("()=>document.querySelector('#sheet-body').innerText")
            if any(w in tx for w in ['NaN','undefined','Infinity']):bad.append(tx[:200])
            ends+=1;await f.evaluate("()=>document.querySelector('#sh-next').click()");await asyncio.sleep(.2);continue
        k=await f.evaluate("()=>{const bs=[...document.querySelectorAll('#actions button')];if(!bs.length)return -1;const t=b=>b.innerText;const pre=!game.hand.board.length;let i=bs.findIndex(b=>/^체크/.test(t(b)));if(i<0&&pre)i=bs.findIndex(b=>/^(콜|림프)/.test(t(b))&&!/allin/.test(b.className));if(i<0)i=bs.findIndex(b=>/^폴드/.test(t(b)));return i<0?0:i}")
        if k>=0:
            lab=await f.evaluate("()=>document.querySelector('#actions').innerText")
            if 'GTO' in lab or '%' in lab and '팟' not in lab:bad.append('hint? '+lab)
            await f.evaluate("(k)=>document.querySelectorAll('#actions button')[k].click()",k);acts+=1;await asyncio.sleep(.1);continue
        await asyncio.sleep(.25)
        if await f.evaluate("()=>!document.querySelector('#b-start').hidden&&!document.querySelector('#actions button')&&!document.querySelector('#sh-next')") and acts==0 and ends==0:
            await f.evaluate("()=>document.querySelector('#b-start').click()")
    return ends,acts,bad
async def main():
    srv=start_server();store['meta/season']={'v':0};store['meta/gtable']={'start':40,'regrant':'day','prec':'fast','diff':'hard','at':1};ok=True
    def chk(name,cond,info=''):
        nonlocal ok;print('PASS' if cond else 'FAIL',name,info);ok=ok and bool(cond)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        adm=await mkpage(b,{'anon':'a_adm','google':{'uid':'g_owner','email':ADMIN}})
        await adm.click('#admIn');await settle(1);await adm.click('#adGo');await asyncio.sleep(.3)
        await adm.fill('#accin','abcd1');await adm.click('#accf button[type=submit]');await settle()
        pa=await mkpage(b,{'anon':'u_pa'},vp=(390,844));await open_join(pa,'new');await submit(pa,'abcd1','테이블러','1234')
        uid=await pa.evaluate("()=>LB.uid");chk('가입',bool(uid))
        await pa.evaluate("()=>{MENUTAB='home';menu()}");await asyncio.sleep(.2)
        card=await pa.evaluate("()=>{const b=document.getElementById('goGt');return b?b.innerText:''}")
        chk('홈에 GTO 홀덤 테이블 카드',('GTO 홀덤 테이블' in card) and ('40BB' in card),card.replace('\n',' '))
        await pa.screenshot(path=SHOT+'w_home.png')
        f=await open_table(pa)
        chk('테이블 화면이 앱 안에서 열림',bool(f) and bool(await pa.query_selector('#gtov iframe')))
        lbl=await f.evaluate("()=>document.querySelector('#b-start').innerText")
        chk('처음 40BB로 시작',('40.0BB' in lbl),lbl)
        await settle(.3)
        d0=store.get('gtable/'+uid) or {}
        chk('내 계정에 스택 기록 생성',d0.get('s')==40 and d0.get('life')==1 and d0.get('name')=='테이블러',json.dumps(d0,ensure_ascii=False)[:160])
        body=await f.evaluate("()=>document.body.innerText")
        chk('힌트·승률·레인지 보기 없음',not await f.query_selector('#b-hint') and not await f.query_selector('#b-vrange') and '에퀴티' not in body and 'GTO 힌트' not in body)
        chk('금지 표현 없음(상금·현금·경품·환전·ICM)',not any(w in body for w in ['상금','현금','경품','환전','ICM']))
        # 빌런 성향 저장
        await f.evaluate("()=>document.getElementById('b-set').click()");await asyncio.sleep(.3)
        rows=await f.evaluate("()=>document.querySelectorAll('.vrow').length")
        chk('빌런 8명 성향 칸',rows==8,rows)
        await f.select_option('#s-v3','aggro');await f.select_option('#s-v7','station');await f.evaluate("()=>document.getElementById('s-save').click()");await settle(1)
        st=(store.get('gtable/'+uid) or {}).get('st') or []
        chk('성향이 내 계정에 저장',len(st)==8 and st[3]=='aggro' and st[7]=='station',st)
        # 몇 핸드 치기
        await f.evaluate("()=>document.querySelector('#b-start').click()")
        ends,acts,bad=await play(f,6)
        await settle(1.2)
        d1=store.get('gtable/'+uid) or {}
        a=await f.evaluate("()=>({s:A.s,h:A.h,th:A.th})")
        chk('핸드 진행·결과 화면 문구 이상 없음',ends>=3 and not [x for x in bad if x!='BUST'],(ends,acts,bad[:2]))
        chk('스택·핸드 수가 계정에 저장',a['s']>0 and abs(d1.get('s',-1)-a['s'])<0.01 and d1.get('th')==a['th'] and a['th']>=3,(d1.get('s'),d1.get('th'),a))
        await pa.screenshot(path=SHOT+'w_table.png')
        # 플랍부터 BB 직접 베팅: 크기 칸(−/+·슬라이더·1/3~팟·올인) → 솔버 기본 크기가 아니면 그 크기로 다시 계산 → 빌런이 대응
        done=None;t0=time.time()
        while done is None and time.time()-t0<200:
            if await f.evaluate("()=>!!document.querySelector('#bz-quiz')"):break
            if await f.evaluate("()=>{const b=document.querySelector('#sh-next');return !!(b&&b.offsetParent)}"):
                await f.evaluate("()=>document.querySelector('#sh-next').click()");await asyncio.sleep(.2);continue
            if await f.evaluate("()=>!document.getElementById('sizer').hidden&&!!document.getElementById('act-size')"):
                z=await f.evaluate("()=>({min:+document.getElementById('sz-r').min,max:+document.getElementById('sz-r').max,lbl:document.getElementById('sizer').innerText})")
                await f.evaluate("()=>document.querySelector('#sizer [data-p=\"4\"]').click()");pot_v=await f.evaluate("()=>+document.getElementById('sz-in').value")
                want=round(min(z['max'],max(z['min'],z['min']+(z['max']-z['min'])*0.37)),1)
                await f.fill('#sz-in',str(want));await f.evaluate("()=>document.getElementById('sz-in').dispatchEvent(new Event('change'))")
                btn=await f.evaluate("()=>document.getElementById('act-size').innerText")
                await pa.screenshot(path=SHOT+'w_sizer.png')
                await f.evaluate("()=>document.getElementById('act-size').click()")
                for _ in range(120):
                    await asyncio.sleep(.5)
                    lg=await f.evaluate("()=>game.hand.log.filter(l=>l.hero).map(l=>l.text)")
                    if lg and any(('%.1f'%want) in x for x in lg[-1:]):break
                    if await f.evaluate("()=>!!document.querySelector('#sh-next')&&!!document.querySelector('#sh-next').offsetParent"):break
                done=(want,btn,lg[-1] if lg else '',z,pot_v);break
            k=await f.evaluate("()=>{const bs=[...document.querySelectorAll('#actions button')];if(!bs.length)return -1;const t=b=>b.innerText;const pre=!game.hand.board.length;let i=bs.findIndex(b=>/^체크/.test(t(b)));if(i<0&&pre)i=bs.findIndex(b=>/^(콜|림프)/.test(t(b))&&!/allin/.test(b.className));if(i<0)i=bs.findIndex(b=>/^폴드/.test(t(b)));return i<0?0:i}")
            if k>=0:await f.evaluate("(k)=>document.querySelectorAll('#actions button')[k].click()",k)
            await asyncio.sleep(.25)
        chk('플랍부터 BB 직접 베팅(입력한 크기 그대로)',bool(done) and ('%.1f'%done[0]) in done[2] and ('%.1fBB'%done[0]) in done[1] and '팟' in done[3]['lbl'],done and (done[0],done[1].replace('\n',' '),done[2]))
        errs_now=await f.evaluate("()=>window.__errs||[]")
        # 닫았다 다시 열면 같은 스택
        await pa.click('#gtClose');await asyncio.sleep(.4)
        card2=await pa.evaluate("()=>document.getElementById('goGt').innerText")
        chk('홈 카드에 내 스택·오늘 핸드',('내 스택' in card2) and ('오늘' in card2),card2.replace('\n',' '))
        f=await open_table(pa);s_now=(store.get('gtable/'+uid) or {}).get('s')
        lbl=await f.evaluate("()=>document.querySelector('#b-start').innerText")
        chk('다시 열면 같은 스택으로 이어서',f'{s_now:.1f}BB' in lbl,(lbl,s_now))
        # 규칙 게시 전(계정 저장 막힘)에도 게임은 됨: 이 기기에 저장 → 규칙이 열리면 계정으로 옮김
        import harness2 as H
        H.DENY.add('gtable');before=dict(store['gtable/'+uid])
        await pa.click('#gtClose');await asyncio.sleep(.3);f=await open_table(pa)
        ok1=await f.evaluate("()=>!!document.querySelector('#b-start:not([hidden])')")
        await f.evaluate("()=>document.querySelector('#b-start').click()");e2,a2,b2=await play(f,2,120);await asyncio.sleep(1)
        th_local=await f.evaluate("()=>A.th");toast_t=await f.evaluate("()=>document.getElementById('toast').innerText")
        chk('계정 저장이 막혀도 게임 진행(이 기기에 저장)',ok1 and e2>=1 and th_local>before.get('th',0) and store['gtable/'+uid].get('th')==before.get('th'),(ok1,e2,th_local,toast_t[:30]))
        H.DENY.discard('gtable')
        await pa.click('#gtClose');await asyncio.sleep(.3);f=await open_table(pa);await asyncio.sleep(.3)
        await f.evaluate("()=>document.querySelector('#b-start').click()");await play(f,1,90);await settle(1.2)
        chk('규칙이 열리면 이 기기 기록이 계정으로',(store['gtable/'+uid].get('th') or 0)>th_local-0.5,(store['gtable/'+uid].get('th'),th_local))
        # 다른 사람 기록은 못 읽음 · 잘못된 값 거부
        pb=await mkpage(b,{'anon':'u_pb'});await open_join(pb,'new');await submit(pb,'abcd1','옆자리','5678')
        r=await pb.evaluate("async(u)=>{try{await LB.db.doc('gtable/'+u).get();return 'read'}catch(e){return 'denied'}}",uid)
        chk('남의 GTO 테이블 기록은 못 읽음',r=='denied',r)
        uidb=await pb.evaluate("()=>LB.uid")
        r2=await pb.evaluate("async(u)=>{try{await LB.db.doc('gtable/'+u).set({name:'x',s:200000,h:0,best:0,ev:0,dn:0,good:0,life:1,lh:0,bn:0,bust:0,day:0,dh:0,th:0,st:[],at:1});return 'ok'}catch(e){return 'denied'}}",uidb)
        chk('말이 안 되는 스택은 저장 거부',r2=='denied',r2)
        # 탈락: 스택 0 → 탈락 화면, 핸드 퀴즈로
        d=dict(store['gtable/'+uid]);d.update({'s':0,'bust':int(time.time()*1000),'bn':1,'lh':d.get('h',0)});store['gtable/'+uid]=d;await broadcast()
        await pa.click('#gtClose');await asyncio.sleep(.3);f=await open_table(pa)
        bz=await f.evaluate("()=>document.querySelector('.nextbox')?document.querySelector('.nextbox').innerText:''")
        chk('탈락 화면·다음 받는 때(내일 0시)','내일 0시' in bz and '0BB' in await f.evaluate("()=>document.body.innerText"),bz.replace('\n',' ')[:60])
        await pa.screenshot(path=SHOT+'w_bust.png')
        try:await f.evaluate("()=>{setTimeout(()=>document.getElementById('bz-quiz').click(),50)}")
        except Exception:pass
        await asyncio.sleep(.8)
        chk('핸드 퀴즈 하러 가기',await pa.evaluate("()=>SCREEN")=='hand' and not await pa.query_selector('#gtov'))
        await pa.evaluate("()=>{qTimerStop();MENUTAB='home';menu()}");await asyncio.sleep(.3)
        c1=await pa.evaluate("()=>document.getElementById('goGt').innerText.replace(/\\n/g,' ')")
        chk('홈 카드: 오늘 탈락이면 다음 받는 때',('탈락' in c1) and ('내일 0시' in c1),c1)
        # 어제 탈락했으면 오늘 새 40BB
        d=dict(store['gtable/'+uid]);d['bust']=int(time.time()*1000)-2*86400000;store['gtable/'+uid]=d;await broadcast();await asyncio.sleep(.4)
        await pa.evaluate("()=>{MENUTAB='home';menu()}");await asyncio.sleep(.2)
        c2=await pa.evaluate("()=>document.getElementById('goGt').innerText.replace(/\\n/g,' ')")
        chk('홈 카드: 다시 받는 때가 지나면 새 40BB 안내',('새 40BB를 받을 수 있어요' in c2),c2)
        f=await open_table(pa);await settle(.6)
        d2=store['gtable/'+uid]
        chk('다음 날 새 40BB(판 수 +1)',d2.get('s')==40 and d2.get('life')==2 and d2.get('h')==0 and d2.get('bn')==1,(d2.get('s'),d2.get('life'),d2.get('h')))
        # 관리자: 설정·통계·스택 되돌리기
        d=dict(store['gtable/'+uid]);d.update({'s':0,'bust':int(time.time()*1000),'bn':2});store['gtable/'+uid]=d;await broadcast()
        await adm.evaluate("()=>adminScreen()");await asyncio.sleep(1)
        sec=await adm.evaluate("()=>document.getElementById('adGt').innerText")
        chk('관리자 GTO 테이블 섹션(난이도·정밀도·시작 스택·다시 받기·플레이어)',all(w in sec for w in ['난이도','솔버 정밀도','시작 스택','탈락 뒤 다시 받기','테이블러','탈락']),sec[:80].replace('\n',' '))
        on=await adm.evaluate("()=>[...document.querySelectorAll('#adGt .gseg button.on')].map(b=>b.innerText)")
        chk('현재 설정 표시(어려움·빠름·40BB·매일 0시)',on==['어려움','빠름','40BB','매일 0시'],on)
        await adm.click('#adGt [data-gk="prec"][data-gv="precise"]');await settle(.8)
        chk('정밀도 정밀로 저장',(store.get('meta/gtable') or {}).get('prec')=='precise')
        await adm.click(f'#adGt [data-gr="{uid}"]');await asyncio.sleep(.2)
        armed=await adm.evaluate("(u)=>document.querySelector('#adGt [data-gr=\"'+u+'\"]').innerText",uid)
        await adm.click(f'#adGt [data-gr="{uid}"]');await settle(.8)
        d3=store['gtable/'+uid]
        chk('스택 되돌리기(두 번 눌러 확인)','한 번 더' in armed and d3.get('s')==40 and d3.get('bust')==0,(armed,d3.get('s')))
        await adm.screenshot(path=SHOT+'w_admin.png',full_page=True)
        # 플레이어 쪽 설정 값: 관리자 정밀도가 테이블에 전달
        f=await open_table(pa)
        pc=await f.evaluate("()=>cfg().prec")
        chk('관리자 설정이 테이블에 전달(정밀)',pc=='precise',pc)
        await b.close()
    srv.shutdown()
    print('결과:','모두 통과' if ok else '실패 있음');sys.exit(0 if ok else 1)
asyncio.run(main())
