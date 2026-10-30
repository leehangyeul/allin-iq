# 핸드 복기(C안): 홈 카드 → 복기 화면(겹쳐 열기) → 예시 핸드 해설 → 홈으로 돌아오기, 하단 메뉴 4칸 유지, 넘침·NaN 없음
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
            await pg.evaluate("()=>{MENUTAB='home';menu()}");await asyncio.sleep(.1)
            r=await pg.evaluate("()=>({card:!!document.getElementById('goRv'),nav:document.querySelectorAll('#panel .mnav button').length,ov:document.documentElement.scrollWidth-document.documentElement.clientWidth})")
            if not r['card']:bad.append(f'{w}px: 홈에 복기 카드 없음')
            if r['nav']!=4:bad.append(f'{w}px: 하단 메뉴 {r["nav"]}칸')
            if r['ov']>0:bad.append(f'{w}px: 홈 가로 넘침')
            await pg.evaluate("()=>document.getElementById('goRv').click()");await asyncio.sleep(1.5)
            fr=None
            for f in pg.frames:
                if f.url.endswith('review/index.html'):fr=f
            if not fr:bad.append(f'{w}px: 복기 화면이 안 열림');continue
            await fr.wait_for_selector('#hand-review',timeout=8000)
            solo=await fr.evaluate("()=>document.documentElement.classList.contains('solo')")
            if solo:bad.append('앱 안에서 열었는데 홈 링크가 보임')
            await fr.evaluate("()=>document.getElementById('hr-ex').click()");await asyncio.sleep(1)
            q=await fr.evaluate("()=>({rp:!document.getElementById('hr-replay').hidden,txt:document.body.innerText,ov:document.documentElement.scrollWidth-document.documentElement.clientWidth})")
            if not q['rp']:bad.append(f'{w}px: 예시 핸드 해설이 안 나옴')
            if re.search(r'NaN|undefined|\[object',q['txt']):bad.append(f'{w}px: 해설에 NaN/undefined')
            for word in ('상금','현금','경품','환전'):
                if word in q['txt']:bad.append(f'복기 화면에 "{word}"')
            if q['ov']>0:bad.append(f'{w}px: 복기 화면 가로 넘침 {q["ov"]}')
            await pg.evaluate("()=>document.getElementById('hrClose').click()");await asyncio.sleep(.2)
            if await pg.query_selector('#hrov'):bad.append('닫기 후에도 복기 화면이 남음')
            if not await pg.query_selector('#goRv'):bad.append('닫은 뒤 홈이 아님')
        # 따로 열었을 때는 앱으로 돌아가는 링크가 보임
        p2=await b.new_page();await p2.goto('http://127.0.0.1:8765/review/index.html');await asyncio.sleep(.5)
        if not await p2.evaluate("()=>document.documentElement.classList.contains('solo')"):bad.append('따로 열었을 때 홈 링크 없음')
        bad+=[e for e in pg.errs if 'ERR_FAILED' not in e]
    print('OK' if not bad else 'FAIL '+str(bad[:10]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
