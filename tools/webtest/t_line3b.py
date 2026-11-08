# 3벳 라인 대본(11/7 IP 5핸드, 11/8 OOP 15핸드): 프리플랍 1순위(3벳)면 새 3벳 라인 — 콜러(빌런)가 플랍에서 먼저 베팅하지 않음,
# 콜을 고르면 원래 콜 라인 대본이 그대로(계산 모드 아님), 보드는 같고 빌런 카드는 라인별, 다음 판에 원본이 바뀌지 않음.
import asyncio,sys,os,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
KEYS=["CO|Q♠Q♦|UTG+1","CO|J♠J♦|UTG+1","LJ|A♣Q♣|MP","CO|Q♣9♣|MP","BB|K♣9♣|SB","BB|5♠5♦|BTN","BB|5♠4♠|BTN","BB|T♠9♠|BTN","BB|9♠7♠|LJ","BB|A♥5♠|BTN","SB|Q♥9♥|BTN","BB|K♠T♠|UTG","SB|A♥T♣|BTN","BB|J♥J♦|UTG+1","SB|Q♠J♠|CO","SB|A♦3♦|BTN","BB|5♥4♥|BTN","BB|A♣3♣|UTG+1","BB|9♥8♥|CO","BB|A♦4♦|BTN"]
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[];info=[]
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn');await asyncio.sleep(1)
        n=await pg.evaluate("(ks)=>ks.filter(k=>LEVELS[0].hands.some(h=>h.me+'|'+h.hand.join('')+'|'+h.vs===k&&h.alt)).length",KEYS)
        if n!=len(KEYS):bad.append(f'3벳 라인 적용 {n}/{len(KEYS)}')
        for k in KEYS:
            for line in ('raise','call'):
                await pg.evaluate("(k)=>{start(0);order[hi]=LEVELS[0].hands.find(h=>h.me+'|'+h.hand.join('')+'|'+h.vs===k);newHand()}",k)
                acts=[]
                for step in range(12):
                    st=await pg.evaluate("()=>{const c=G.sub||G.cur;if(!document.querySelector('#panel button[data-k]'))return null;const mo=mergedOF(c);return{a:c.a,top:bestOf(mo.o,mo.f),si,cx:G.cx,alt:!!G.alt,first:!!c.first}}")
                    if not st:break
                    kk=line if st['si']==0 else st['top']
                    acts.append((st['si'],st['a'],kk,st['cx'],st['first']))
                    await pg.evaluate("(k)=>document.querySelector('#panel button[data-k=\"'+k+'\"]').click()",kk)
                r=await pg.evaluate("()=>({ended:G.ended,vh:order[hi].vh.join(''),src:order[hi].__src.vh.join(''),alt:order[hi].__src.alt.vh.join(''),n:G.dec.length,cx:G.cx,big:(document.querySelector('.scr .big')||{}).innerText||''})")
                flop=[a for a in acts if a[0]==1]
                if line=='raise' and flop and re.match(r'빌런 \d+% 베팅|빌런 올인',flop[0][1]):bad.append(f'{k} 3벳 라인 플랍 동크: {flop[0][1]}')
                fi=next((j for j,a in enumerate(acts) if a[4] and a[2]!='check'),len(acts))  # OOP 첫 행동에서 베팅하면 계산 모드가 맞음
                if any(a[3] for a in acts[:fi+1]):bad.append(f'{k} {line}: 1순위대로 쳤는데 계산 모드')
                if r['vh']!=(r['alt'] if line=='call' else r['src']):bad.append(f'{k} {line} 라인 빌런 카드가 안 맞음')
                if not r['big']:bad.append(f'{k} {line} 결과 없음')
                info.append((k,line,[a[1][:18] for a in acts],r['vh'],r['big']))
        # 원본 보존: 콜 라인 뒤에도 원본 3벳 라인 그대로
        ok=await pg.evaluate("()=>{const h=LEVELS[0].hands.find(h=>h.me==='CO'&&h.hand.join('')==='Q♠Q♦');return h.s[1].a.startsWith('빌런 체크')&&h.vh.join('')==='A♠J♠'}")
        if not ok:bad.append('원본 핸드가 바뀜')
        bad+=[e for e in pg.errs if 'ERR_FAILED' not in e][:3]
    for x in info:print(x)
    print('OK' if not bad else 'FAIL '+str(bad));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
