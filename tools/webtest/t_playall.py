# 모든 핸드를 여러 선택 경로로 끝까지 풀고, 연습 문제도 많이 풀어서 NaN·undefined·점수 범위·표시 불일치를 찾아요
import asyncio,sys,os,random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    random.seed(7);srv=start_server();store['meta/season']={'v':0}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1)
        await pg.set_viewport_size({'width':390,'height':844})
        n=await pg.evaluate("()=>{start(0);return LEVELS[0].hands.length}")
        bad=[];runs=0
        for hi in range(n):
            for path in range(4):
                await pg.evaluate("(i)=>{start(0);order[hi]=LEVELS[0].hands[i];newHand()}",hi)
                for _ in range(12):
                    keys=await pg.evaluate("()=>[...document.querySelectorAll('#panel button[data-k]')].map(x=>x.dataset.k)")
                    if not keys:break
                    k=keys[path%len(keys)] if path<2 else random.choice(keys)
                    await pg.evaluate("(k)=>document.querySelector('#panel button[data-k=\"'+k+'\"]').click()",k)
                r=await pg.evaluate("""()=>{const h=order[hi],t=document.getElementById('panel').innerText+document.getElementById('stage').innerText;
                  const big=(document.querySelector('.scr .big')||{}).innerText;const dlv=(document.querySelector('.dlv')||{}).innerText||'';
                  return {id:h.me+' '+h.hand.join(''),big,dlv,ended:G.ended,dec:G.dec.length,
                   nan:/NaN|undefined|null|\\[object/.test(t),run:document.querySelectorAll('.bb .pc.run').length}}""")
                runs+=1
                sc=int((r['big'] or 'x').split('/')[0].strip()) if r['big'] and r['big'].split('/')[0].strip().isdigit() else None
                if sc is None:bad.append(f"{r['id']} 경로{path}: 결과 점수 없음");continue
                if not 0<=sc<=100:bad.append(f"{r['id']} 점수 범위 밖 {sc}")
                if r['nan']:bad.append(f"{r['id']} 경로{path}: 화면에 NaN/undefined")
                if f"결정 {r['dec']}번" not in r['dlv']:bad.append(f"{r['id']} 결정 수 표기 불일치 {r['dlv']!r} vs {r['dec']}")
                if r['ended']=='allin' and r['run']:bad.append(f"{r['id']} 올인 종료인데 흐린 카드 {r['run']}장")
        print(f'핸드 {n}개 × 4경로 = {runs}판 풀이')
        # drills
        dn=0
        for i in range(400):
            r=await pg.evaluate("""()=>{drillNext();const sp=DS.sp;const l=['f','r','c','j'][Math.floor(Math.random()*4)];
              const a=DSTATS.sum,c=DSTATS.n;drillAnswer(l);const t=document.getElementById('panel').innerText;
              return {n:DSTATS.n-c,add:DSTATS.sum-a,nan:/NaN|undefined|null|\\[object/.test(t),k:sp.kind+':'+sp.spot+':'+sp.pos+':'+sp.st}}""")
            dn+=1
            if r['n']!=1:bad.append(f"연습 {r['k']} 기록 {r['n']}건")
            if not 0<=r['add']<=100:bad.append(f"연습 {r['k']} 점수 {r['add']}")
            if r['nan']:bad.append(f"연습 {r['k']} 화면에 NaN/undefined")
        print(f'연습 {dn}문제 풀이')
        print('\n'.join(sorted(set(bad))) or '이상 없음');print('콘솔 오류',[e for e in pg.errs if 'ERR_FAILED' not in e]);await b.close()
    srv.shutdown()
asyncio.run(main())
