# 기준 규칙(자료 A rev 35, 10/29): ① 20~34bb에서 IP가 앞·중간 포지션(UTG~HJ) 오픈에 3벳 올인을 정답으로 쓰지 않음(작은 3벳)
# ② 32~55bb의 4벳은 올인이 아님(3벳의 약 2배) — 퀴즈에 '4벳 올인' 선택지가 그 구간에 없어야 함. ③ 해당 핸드를 3벳으로 끝까지 풀 수 있음
import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn');await asyncio.sleep(1)
        r=await pg.evaluate("""()=>{const out=[];const EP=['UTG','UTG+1','UTG+2','MP','LJ','HJ'],ORD=['UTG','UTG+1','UTG+2','MP','LJ','HJ','CO','BTN','SB','BB'];let n=0;
          LEVELS[0].hands.forEach((h,i)=>{const D=h.d||100;h.s.forEach((st,si)=>{
            if(D>=32&&D<=55&&st.o.some(x=>/4벳/.test(x[1])&&(x[0]==='jam'||/올인/.test(x[1]))))out.push(`${i} ${h.me} ${D}bb 4벳 올인 선택지`);
            if(si===0&&D>=20&&D<35&&h.pf[1]>1&&!h.multi&&!/올인|3벳|4벳/.test(st.a)){const ip=ORD.indexOf(h.me)>ORD.indexOf(h.vs)&&!['SB','BB'].includes(h.me);
              if(ip&&EP.includes(h.vs)){n++;if((+st.f.jam||0)>0)out.push(`${i} ${h.me} vs ${h.vs} ${D}bb 3벳 올인 ${st.f.jam}%`)}}
          })});return {out,n}}""")
        bad+=r['out'];print('20~34bb IP vs 앞·중간 오픈 문제',r['n'],'개 확인')
        # 해당 핸드(QQ) 3벳으로 끝까지
        ok=await pg.evaluate("""async()=>{const i=LEVELS[0].hands.findIndex(h=>h.me==='CO'&&h.vs==='UTG+1'&&h.hand.join('')==='Q♠Q♦');start(0);order[hi]=LEVELS[0].hands[i];newHand();
          document.querySelector('#panel button[data-k="raise"]').click();for(let k=0;k<12;k++){await new Promise(r=>setTimeout(r,30));const b=document.querySelector('#panel button[data-k]');if(!b)break;b.click()}
          return {n:STATS.n,big:(document.querySelector('.scr .big')||{}).innerText||'',t:/NaN|undefined/.test(document.getElementById('panel').innerText)}}""")
        if ok['n']<1 or not ok['big'] or ok['t']:bad.append(f'QQ 3벳 경로 이상 {ok}')
        bad+=[e for e in pg.errs if 'ERR_FAILED' not in e]
    print('OK' if not bad else 'FAIL '+str(bad[:10]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
