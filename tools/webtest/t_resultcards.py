# 결과 카드(F안): 150핸드 × 2경로, 요약→스트리트 카드 넘기기, 접이식 전부 펼침, NaN·가로 넘침 없음, 다음 핸드 동작
import asyncio,sys,os,random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1)
        await pg.set_viewport_size({'width':390,'height':844})
        n=await pg.evaluate("()=>{start(0);return LEVELS[0].hands.length}")
        random.seed(5)
        for hi in range(0,n,3):
            await pg.evaluate("(i)=>{start(0);order[hi]=LEVELS[0].hands[i];newHand()}",hi)
            for _ in range(12):
                keys=await pg.evaluate("()=>[...document.querySelectorAll('#panel button[data-k]')].map(x=>x.dataset.k)")
                if not keys:break
                await pg.evaluate("(k)=>document.querySelector('#panel button[data-k=\"'+k+'\"]').click()",random.choice(keys))
            dec=await pg.evaluate("()=>G.dec.length")
            if not await pg.query_selector('#rcgo'):bad.append(f"{hi}: 요약 카드 없음");continue
            await pg.evaluate("()=>document.getElementById('rcgo').click()")
            for k in range(dec):
                await pg.evaluate("()=>new Promise(r=>setTimeout(r,250))")
                for _ in range(10):
                    c=await pg.evaluate("()=>{const e=document.querySelector('[aria-expanded=\"false\"]');if(e)e.click();return !!e}")
                    if not c:break
                r=await pg.evaluate("()=>{const t=document.getElementById('panel').innerText;return {nan:/NaN|undefined|null|\\[object/.test(t),ov:document.documentElement.scrollWidth-document.documentElement.clientWidth,n:document.querySelectorAll('.rcsec').length,load:/계산 중/.test(t)}}")
                if r['nan']:bad.append(f"{hi} 카드{k+1}: NaN/undefined")
                if r['ov']>0:bad.append(f"{hi} 카드{k+1}: 가로 넘침 {r['ov']}")
                if r['n']<2:bad.append(f"{hi} 카드{k+1}: 접이식 {r['n']}개")
                if r['load']:bad.append(f"{hi} 카드{k+1}: 계산 중에서 안 끝남")
                if k<dec-1:await pg.evaluate("()=>document.getElementById('rcfw').click()")
            # last page: next hand button
            if not await pg.query_selector('#next'):bad.append(f"{hi}: 마지막 카드에 다음 핸드 없음")
            else:
                c=await pg.evaluate("()=>hi");await pg.evaluate("()=>document.getElementById('next').click()");await asyncio.sleep(.1)
                if await pg.evaluate("()=>hi")!=c+1 and await pg.evaluate("()=>SCREEN")=='hand' and not await pg.query_selector('#panel button[data-k]'):bad.append(f"{hi}: 다음 핸드 안 넘어감")
    if errs:bad.append(f"JS 오류 {errs[:2]}")
    print("FAIL" if bad else "OK",bad[:15]);srv.shutdown()
    sys.exit(1 if bad else 0)
asyncio.run(main())
