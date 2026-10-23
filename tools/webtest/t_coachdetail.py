# 코치 상세 분석: 기록 항목(행동·GTO 비율·상황·핸드 강도·EV) 저장, EV 계산 값, 화면(요약·접이식·! 설명), 잠금, 기기 간 합치기
import asyncio,sys,os,json,random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EV=json.load(open(os.path.join(ROOT,'tools','gen150','own','hu_ev.json')))
POSG=["UTG","UTG+1","UTG+2","LJ","HJ","CO","BTN","SB","BB"]
def fake(n,seed=3):
    random.seed(seed);out=[];i=0
    for hh in range(1,n//2+1):
        u=f"{1700000000000+hh}.t"
        for s in range(random.choice([1,2,3])):
            k=random.choice("FPAJ");g=[random.choice([0,10,30,60]) for _ in range(4)]
            r={"i":hh,"u":u,"p":random.choice(POSG),"st":random.choice([100,40,25,15,10]),"s":s,"sc":random.choice([0,30,60,80,100,100]),"pf":None,"fo":0,"to":0,"k":k,"g":g,"sit":random.choice("obptmf")}
            if s==0:
                r["t"]=random.choice(["top","strong","mid","weak","trash"])
                if r["sit"]=="f" and r["p"] in("SB","BB"):r["ev"]=random.choice([0,0,0.4,1.2]);r["hc"]=random.choice(["88","K9o","43s"])
            out.append(r)
    return out
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn2' if await pg.query_selector('#admIn2') else '#admIn');await asyncio.sleep(1)
        await pg.set_viewport_size({'width':390,'height':844})
        # 1) 150문제 모두 상황 구분이 있고, EV 대상은 12개
        r=await pg.evaluate("()=>{start(0);const H=LEVELS[0].hands;return{n:H.length,miss:H.filter(h=>!HSIT[h.me+'|'+h.hand.join('')]).length,ev:H.filter(h=>HEV.indexOf(h.me+'|'+h.hand.join(''))>=0).length,sit:[...new Set(Object.values(HSIT))].sort().join('')}}")
        print('상황 구분',r)
        if r['n']!=150 or r['miss'] or r['ev']!=12 or r['sit']!='bfmopt':bad.append(f'상황/EV 대상 표 이상 {r}')
        # 2) 실제로 풀어서 기록 확인 + EV 값 독립 계산과 비교
        n=r['n'];checked=0;evchk=0
        for hi in range(n):
            for path in (0,1):
                await pg.evaluate("(i)=>{start(0);order[hi]=LEVELS[0].hands[i];newHand()}",hi)
                for _ in range(12):
                    keys=await pg.evaluate("()=>[...document.querySelectorAll('#panel button[data-k]')].map(x=>x.dataset.k)")
                    if not keys:break
                    k=keys[path%len(keys)]
                    await pg.evaluate("(k)=>document.querySelector('#panel button[data-k=\"'+k+'\"]').click()",k)
                info=await pg.evaluate("""()=>{const h=order[hi];const u=CL.h[CL.h.length-1].u;const rs=CL.h.filter(x=>x.u===u);
                  return{me:h.me,hand:h.hand,d:G.D,ev:HEV.indexOf(h.me+'|'+h.hand.join(''))>=0,rs,dec:G.dec.map(d=>d.k)}}""")
                rs=info['rs'];checked+=1
                if len(rs)!=len(info['dec']):bad.append(f"{info['me']} {info['hand']}: 기록 {len(rs)} != 결정 {len(info['dec'])}");continue
                for j,x in enumerate(rs):
                    if x.get('k') not in list('FPAJ') or not isinstance(x.get('g'),list) or len(x['g'])!=4:bad.append(f"{info['me']} {info['hand']}: k/g 이상 {x}");continue
                    if abs(sum(x['g'])-100)>3:bad.append(f"{info['me']} {info['hand']}: g 합 {sum(x['g'])}")
                    if x['k']!={'fold':'F','call':'P','check':'P','jam':'J'}.get(info['dec'][j],'A'):bad.append(f"{info['me']} {info['hand']}: 고른 행동 불일치 {x['k']} vs {info['dec'][j]}")
                    if not x.get('sit'):bad.append(f"{info['me']} {info['hand']}: 상황 없음")
                    if (j==0)!=('t' in x):bad.append(f"{info['me']} {info['hand']}: 핸드 강도는 첫 결정에만 있어야 해요 {j} {x}")
                if info['ev']:
                    x=rs[0];hc=x.get('hc')
                    if hc is None or x.get('ev') is None:bad.append(f"{info['me']} {info['hand']}: EV 누락 {x}");continue
                    gain=EV[str(info['d'])]['sb' if info['me']=='SB' else 'bb'][hc]
                    took=info['dec'][0] in('jam','call')
                    exp=round((max(gain,0)-(gain if took else 0)),2)
                    if abs(x['ev']-exp)>0.011:bad.append(f"{info['me']} {hc} {info['d']}BB {info['dec'][0]}: EV {x['ev']} != {exp}")
                    evchk+=1
                else:
                    if any('ev' in x for x in rs):bad.append(f"{info['me']} {info['hand']}: EV 대상이 아닌데 EV 있음")
        print(f'기록 확인 {checked}판, EV 값 비교 {evchk}판')
        # 3) 합치기 후에도 새 항목이 남아요
        m=await pg.evaluate("""()=>{const x={k:'P',g:[0,100,0,0],sit:'o',t:'mid',ev:0.5,hc:'88'};const o=coachMerge({hn:1,dn:0,h:[{i:1,u:'1.a',p:'BB',st:15,s:0,sc:50,pf:null,fo:0,to:0,...x}],d:[]},null);return o.h[0]}""")
        if m.get('k')!='P' or m.get('ev')!=0.5 or m.get('hc')!='88' or m.get('g')!=[0,100,0,0]:bad.append(f'합치기에서 새 항목 유실 {m}')
        # 4) 상세 화면: 잠금 → 열림
        recs=fake(120)
        await pg.evaluate("(x)=>{CL={hn:60,dn:60,h:x.slice(0,30),d:[]};coachScreen()}",recs)
        t=await pg.evaluate("()=>document.getElementById('cdgo').innerText.replace(/\\n/g,' ')");print('버튼(잠금):',t)
        await pg.evaluate("()=>document.getElementById('cdgo').click()");await asyncio.sleep(.3)
        t=await pg.evaluate("()=>document.getElementById('panel').innerText.replace(/\\n/g,' | ')");print('잠금 화면:',t[:120])
        if '잠겨' not in t:bad.append('새 기록 부족인데 잠기지 않음')
        await pg.evaluate("(x)=>{CL={hn:60,dn:60,h:x,d:[]};coachScreen()}",recs)
        await pg.evaluate("()=>document.getElementById('cdgo').click()");await asyncio.sleep(.4)
        ov=await pg.evaluate("()=>document.documentElement.scrollWidth-document.documentElement.clientWidth")
        if ov>0:bad.append(f'가로 넘침 {ov}')
        top=await pg.evaluate("()=>document.getElementById('panel').innerText")
        for w in ['NaN','undefined','Infinity','null','[object']:
            if w in top:bad.append(f'화면에 {w}')
        for w in ['평균','GTO 일치율','강점','약점','손실','습관','EV','연습']:
            if w not in top:bad.append(f'요약에 {w} 없음')
        print('섹션 수',await pg.evaluate("()=>document.querySelectorAll('.cdsec').length"),'요약 행',await pg.evaluate("()=>document.querySelectorAll('.cdsrow').length"))
        # 요약 행 누르면 해당 항목이 열려요
        await pg.evaluate("()=>document.querySelector('[data-cdgo=cd-ev]').click()");await asyncio.sleep(.5)
        if not await pg.evaluate("()=>document.getElementById('cd-ev').open"):bad.append('요약 행을 눌러도 항목이 안 열림')
        # 모두 펼치기 + ! 전부 눌러서 설명이 나오는지
        await pg.evaluate("()=>document.getElementById('cdall').click()");await asyncio.sleep(.2)
        keys=await pg.evaluate("()=>[...new Set([...document.querySelectorAll('.cdtip')].map(b=>b.dataset.cdk))]")
        miss=[]
        for k in keys:
            await pg.evaluate("(k)=>document.querySelector('.cdtip[data-cdk=\"'+k+'\"]').click()",k)
            d=await pg.evaluate("()=>({t:document.getElementById('cdshT').textContent,d:document.getElementById('cdshD').textContent,h:document.getElementById('cdsheet').hidden})")
            if d['h'] or not d['d'].strip() or not d['t'].strip():miss.append(k)
        print('! 표시',len(keys),'개, 설명 없음',miss)
        bad+= [f'! 설명 없음 {k}' for k in miss]
        await pg.evaluate("()=>document.getElementById('cdshX').click()")
        if not await pg.evaluate("()=>document.getElementById('cdsheet').hidden"):bad.append('설명창 닫기 안 됨')
        full=await pg.evaluate("()=>document.getElementById('panel').innerText")
        for w in ['NaN','undefined','Infinity','[object']:
            if w in full:bad.append(f'펼친 화면에 {w}')
        await pg.screenshot(path='/tmp/t_cd_full.png',full_page=True)
        # 상금·현금·경품·환전·강의 표기 없음
        for w in ['상금 ','현금','경품','환전','PokerCoaching','강의']:
            if w in full:bad.append(f'금지 표현 {w}')
        # 뒤로가기 → 코치 보드
        await pg.evaluate("()=>document.getElementById('back').click()");await asyncio.sleep(.3)
        if await pg.evaluate("()=>SCREEN")!='coach':bad.append('뒤로가기가 코치 보드로 돌아가지 않음')
        # 극단 데이터: 전부 0점 / 전부 100점 / EV 없음
        for name,fn in [('전부0점',"x=>x.map(r=>({...r,sc:0}))"),('전부100점',"x=>x.map(r=>({...r,sc:100}))"),('EV없음',"x=>x.map(r=>{const y={...r};delete y.ev;delete y.hc;return y})")]:
            await pg.evaluate(f"(x)=>{{CL={{hn:60,dn:60,h:({fn})(x),d:[]}};cdScreen()}}",recs);await asyncio.sleep(.2)
            await pg.evaluate("()=>document.getElementById('cdall').click()")
            tt=await pg.evaluate("()=>document.getElementById('panel').innerText")
            for w in ['NaN','undefined','Infinity','[object']:
                if w in tt:bad.append(f'{name}: 화면에 {w}')
        await pg.set_viewport_size({'width':390,'height':844})
        print('\n'.join(sorted(set(bad))) or '이상 없음');print('콘솔 오류',[e for e in pg.errs if 'ERR_FAILED' not in e]);await b.close()
    srv.shutdown()
asyncio.run(main())
