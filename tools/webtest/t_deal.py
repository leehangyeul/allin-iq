# 문제 출제(11/5): 같은 문제는 그 난이도를 한 바퀴 다 보기 전엔 다시 안 나옴(새 판·새로고침 후에도), 비슷한 문제 간격, 난이도 비율 유지
import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn');await asyncio.sleep(1)
        r=await pg.evaluate("""()=>{localStorage.removeItem('hgq-seen');localStorage.removeItem('hgq-recent');
          const played=[];const t0=performance.now();
          // 판을 20번 새로 시작하면서 판마다 15문제씩 = 300문제
          for(let g=0;g<20;g++){deal();for(let i=0;i<15;i++){hi=i;hMarkPlayed(order[i]);played.push(order[i])}}
          const ms=performance.now()-t0;
          const T={1:0,2:0,3:0};LEVELS[0].hands.forEach(h=>T[hTier(h)]++);
          // 같은 문제 재등장: 그 난이도 문제 수보다 짧은 간격이면 실패
          const last={},rep=[];played.forEach((h,i)=>{const k=hKey(h);if(last[k]!=null){const tierSeen=played.slice(last[k]+1,i).filter(x=>hTier(x)===hTier(h)).length;if(tierSeen<Math.floor(T[hTier(h)]/2)-1)rep.push([k,i-last[k]])}last[k]=i});
          // 같은 자리+같은 핸드 40문제 안 재등장
          let near=0;played.forEach((h,i)=>{for(let j=Math.max(0,i-40);j<i;j++){const r=played[j];if(r!==h&&r.me===h.me&&hCls(r)===hCls(h)){near++;break}}});
          let sameCls=0;played.forEach((h,i)=>{for(let j=Math.max(0,i-12);j<i;j++)if(hCls(played[j])===hCls(h)){sameCls++;break}});
          const mix={1:0,2:0,3:0};played.forEach(h=>mix[hTier(h)]++);
          return{rep,near,sameCls,mix,ms:Math.round(ms/20),n:played.length}}""")
        print(r)
        if r['rep']:bad.append(f"같은 문제가 한 바퀴 전에 다시 나옴 {r['rep'][:5]}")
        if r['near']>3:bad.append(f"같은 자리+같은 핸드가 40문제 안에 {r['near']}번")
        if r['sameCls']>15:bad.append(f"같은 핸드가 12문제 안에 {r['sameCls']}번")
        m=r['mix'];tot=sum(m.values())
        if not(0.12<m['1']/tot<0.30 and 0.38<m['2']/tot<0.62 and 0.20<m['3']/tot<0.40):bad.append(f'난이도 비율 이상 {m}')
        if r['ms']>400:bad.append(f"출제 계산이 느림 {r['ms']}ms")
        # 새로고침 뒤에도 기억
        await pg.reload();await asyncio.sleep(1.2)
        k=await pg.evaluate("()=>JSON.parse(localStorage.getItem('hgq-seen')||'[]').length")
        if k<50:bad.append(f'새로고침 후 본 문제 기록이 사라짐 {k}')
        bad+=[e for e in pg.errs if 'ERR_FAILED' not in e]
    print('OK' if not bad else 'FAIL '+str(bad[:10]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
