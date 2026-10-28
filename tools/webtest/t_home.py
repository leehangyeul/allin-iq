# 시작 화면(D안): 점수 링, 큰 버튼, 하단 메뉴 4개(홈·순위·코치·더보기) 이동, 퀴즈 중에는 메뉴 없음, 가로 넘침·NaN 없음
import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn');await asyncio.sleep(1)
        for w in (320,390,430):
            await pg.set_viewport_size({'width':w,'height':844})
            for st in ("{n:0,sum:0,streak:0,best:0}","{n:12,sum:960,streak:2,best:5}","{n:60,sum:5400,streak:0,best:9}"):
                await pg.evaluate("(s)=>{STATS=eval('('+s+')');DSTATS=eval('('+s+')');MENUTAB='home';menu()}",st)
                for tab in ('home','rank','more'):
                    await pg.evaluate("(t)=>{MENUTAB=t;menu()}",tab);await asyncio.sleep(.1)
                    r=await pg.evaluate("()=>({ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,nan:/NaN|undefined|null|\\[object/.test(document.getElementById('panel').innerText),nav:document.querySelectorAll('#panel .mnav button').length,on:(document.querySelector('.mnav .on')||{}).dataset&&document.querySelector('.mnav .on').dataset.mt})")
                    if r['ov']>0:bad.append(f'{w}px {tab}: 가로 넘침 {r["ov"]}')
                    if r['nan']:bad.append(f'{w}px {tab}: NaN/undefined')
                    if r['nav']!=4 or r['on']!=tab:bad.append(f'{w}px {tab}: 하단 메뉴 이상 {r}')
        await pg.set_viewport_size({'width':390,'height':844})
        await pg.evaluate("()=>{STATS={n:3,sum:240,streak:0,best:0};MENUTAB='home';menu()}")
        # 하단 메뉴로 이동
        for mt,exp in [('rank','lbbox'),('more','adGo'),('home','go')]:
            await pg.evaluate("(m)=>document.querySelector('.mnav [data-mt=\"'+m+'\"]').click()",mt);await asyncio.sleep(.2)
            if not await pg.query_selector('#'+exp):bad.append(f'{mt} 탭에 #{exp} 없음')
        # 코치 탭: 코치 화면 + 메뉴 유지
        await pg.evaluate("()=>{MYNAME='하루';document.querySelector('.mnav [data-mt=\"coach\"]').click()}");await asyncio.sleep(.4)
        if await pg.evaluate("()=>SCREEN")!='coach':bad.append('코치 탭이 코치 화면으로 안 감')
        if not await pg.query_selector('#panel .mnav'):bad.append('코치 화면에 하단 메뉴 없음')
        await pg.evaluate("()=>document.querySelector('.mnav [data-mt=\"home\"]').click()");await asyncio.sleep(.2)
        if await pg.evaluate("()=>SCREEN+MENUTAB")!='menuhome':bad.append('코치→홈 이동 실패')
        # 퀴즈 중에는 하단 메뉴 없음, 뒤로가기는 홈
        await pg.evaluate("()=>document.getElementById('go').click()");await asyncio.sleep(.4)
        if await pg.query_selector('.mnav'):bad.append('퀴즈 중에 하단 메뉴가 보임')
        await pg.evaluate("()=>document.getElementById('back').click()");await asyncio.sleep(.2)
        if not await pg.query_selector('#go'):bad.append('뒤로가기가 홈으로 안 감')
        bad+=[e for e in pg.errs if 'ERR_FAILED' not in e]
    print('OK' if not bad else 'FAIL '+str(bad[:10]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
