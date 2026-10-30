# 핸드 복기 가독성: 앱 안 머리글 숨김, 탭 한 줄, 요약 숫자 칸, 한 단계씩 보기에서 전체 해설 숨김, 빌런 결정 접힘, 숫자 강조, 스트리트 머리 고정, 진행 막대, 폭별 넘침 없음
import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn');await asyncio.sleep(1)
        for w in (320,390,430,1280):
            await pg.set_viewport_size({'width':w,'height':844})
            await pg.evaluate("()=>{reviewClose();MENUTAB='home';menu();document.getElementById('goRv').click()}");await asyncio.sleep(1.2)
            fr=[f for f in pg.frames if f.url.endswith('review/index.html')][0];await fr.wait_for_selector('#hand-review')
            r=await fr.evaluate("""()=>{const v=e=>e&&getComputedStyle(e).display!=='none';const tb=[...document.querySelectorAll('.hr-tabs.main button')];
              return {inapp:document.documentElement.classList.contains('inapp'),h1:v(document.querySelector('.app > header h1')),
                tabsOneRow:new Set(tb.map(b=>Math.round(b.getBoundingClientRect().top))).size===1&&tb.length===3,
                steps:!!document.querySelector('#hr-steps .bar')&&document.querySelectorAll('#hr-steps .bar i').length===11}}""")
            if not r['inapp'] or r['h1']:bad.append(f'{w}: 앱 안 머리글 {r}')
            if not r['tabsOneRow']:bad.append(f'{w}: 탭이 한 줄이 아님')
            if not r['steps']:bad.append(f'{w}: 진행 막대 없음')
            await fr.evaluate("()=>document.getElementById('hr-ex').click()");await asyncio.sleep(.8)
            s=await fr.evaluate("""()=>{const st=document.getElementById('hr-story');
              return {tiles:document.querySelectorAll('#hr-story .hr-sum2 .pr').length,heroFirst:(document.querySelector('#hr-story .hr-sum2 .pr')||{}).className,
                how:!!document.querySelector('#hr-story details.hr-how:not([open])'),vit:document.querySelectorAll('#hr-story details.hr-vitem').length,
                vitOpen:document.querySelectorAll('#hr-story details.hr-vitem[open]').length,heroCards:document.querySelectorAll('#hr-story > section .hr-item:not(details .hr-item)').length,
                nums:document.querySelectorAll('#hr-story .hr-detail .n').length,sticky:getComputedStyle(document.querySelector('#hr-story .hr-sst .hd')).position,
                nos:document.querySelectorAll('#hr-story .hr-no').length,txt:st.innerText,ov:document.documentElement.scrollWidth-document.documentElement.clientWidth}}""")
            if s['tiles']<1 or 'h' not in s['heroFirst'].split():bad.append(f'{w}: 요약 칸 {s["tiles"]} {s["heroFirst"]}')
            if not s['how']:bad.append(f'{w}: 계산 방법이 접혀 있지 않음')
            if s['vit']<1 or s['vitOpen']:bad.append(f'{w}: 빌런 결정 접힘 {s["vit"]}/{s["vitOpen"]}')
            if s['nums']<5:bad.append(f'{w}: 숫자 강조 {s["nums"]}')
            if s['sticky']!='sticky':bad.append(f'{w}: 스트리트 머리 고정 안 됨')
            if s['nos']<10:bad.append(f'{w}: 번호 버튼 {s["nos"]}')
            if re.search(r'NaN|undefined|\[object',s['txt']):bad.append(f'{w}: 해설에 NaN')
            if s['ov']>0:bad.append(f'{w}: 가로 넘침 {s["ov"]}')
            # 빌런 결정 펼치기
            await fr.evaluate("()=>document.querySelector('#hr-story details.hr-vitem summary')?.click()");await asyncio.sleep(.1)
            if not await fr.evaluate("()=>!!document.querySelector('#hr-story details.hr-vitem')?.open"):bad.append(f'{w}: 빌런 결정이 안 펼쳐짐')
            # 번호 → 한 단계씩 보기, 전체 해설은 숨김
            await fr.evaluate("()=>(document.querySelectorAll('#hr-story .hr-no')[2]||document.querySelectorAll('#hr-story [data-k]')[2]).click()");await asyncio.sleep(.3)
            q=await fr.evaluate("""()=>({storyShown:document.getElementById('hr-story').getBoundingClientRect().height>0,nav:document.querySelector('.hr-nav').getBoundingClientRect().top-document.getElementById('hr-table').getBoundingClientRect().bottom,
               name:document.getElementById('hr-stepname').innerText,ov:document.documentElement.scrollWidth-document.documentElement.clientWidth})""")
            if q['storyShown']:bad.append(f'{w}: 한 단계씩 보기에 전체 해설이 남음')
            if q['nav']>200:bad.append(f'{w}: 이전·다음 버튼이 멀리 있음 {q["nav"]}')
            if not q['name'].startswith('3 /'):bad.append(f'{w}: 번호로 간 장면 {q["name"]}')
            if q['ov']>0:bad.append(f'{w}: 한 단계 화면 넘침 {q["ov"]}')
            for i in range(20):
                await fr.evaluate("()=>document.getElementById('hr-next').click()")
            t=await fr.evaluate("()=>document.getElementById('hr-evals').innerText+document.getElementById('hr-stepname').innerText")
            if re.search(r'NaN|undefined|\[object',t):bad.append(f'{w}: 한 단계 화면에 NaN')
            # 말풍선이 카드보다 위
            await fr.evaluate("()=>{document.getElementById('hr-v-step').click();document.querySelectorAll('#hr-dots button')[3].click()}");await asyncio.sleep(.2)
            z=await fr.evaluate("()=>{const s=document.querySelector('.hr-say');if(!s)return null;const r=s.getBoundingClientRect();const el=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return el&&(el===s||s.contains(el))}")
            if z is False:bad.append(f'{w}: 말풍선이 가려짐')
        bad+=[e for e in pg.errs if 'ERR_FAILED' not in e]
    print('OK' if not bad else 'FAIL '+str(bad[:12]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
