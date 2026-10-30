# 핸드 복기 팟 계산: 사이드 팟 나누기, 콜받지 않은 베팅 돌려주기, 3명 찹, 최소 레이즈보다 작은 올인 뒤 재레이즈 막기
import asyncio,sys,os,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
RS="23456789TJQKA";SU="shdc"
def cn(s):return RS.index(s[0])*4+SU.index(s[1])
CASES=[
 ({"hero":["UTG","Qh","Qc",20],"vs":[["CO","As","Kd",60],["BB","9s","9d",60]],"acts":["raise:20","call","call","raise:10","call","check","check","check","check"],"board":["2c","7d","Qs","3h","9h"]},
  ["메인 팟 61.5BB 히어로 승","사이드 팟 20BB 빌런2 승"]),
 ({"hero":["BTN","Ah","Kh",100],"vs":[["BB","Js","Jd",30]],"acts":["raise:100","call"],"board":["2c","7d","Qs","3h","9h"]},
  ["빌런1 승 (팟 59.5BB)","콜받지 않은 71BB는 히어로에게 돌아감"]),
 ({"hero":["CO","Ah","Kh",40],"vs":[["BTN","As","Kd",40],["BB","Ac","Kc",15]],"acts":["raise:40","call","call"],"board":["2c","7d","9h","Tc","Jd"]},
  ["메인 팟 43.5BB 히어로·빌런1·빌런2 찹","사이드 팟 52BB 히어로·빌런1 찹"]),
]
async def card(pg,x):await pg.evaluate("(c)=>document.querySelector('#hr-deck button[data-c=\"'+c+'\"]').click()",cn(x))
async def setup(pg,cs):
    await pg.evaluate("()=>document.getElementById('hr-reset').click()")
    h=cs['hero'];await pg.evaluate("(s)=>document.querySelector('#hr-table [data-seat=\"'+s+'\"]').click()",h[0])
    await card(pg,h[1]);await card(pg,h[2])
    await pg.evaluate("(v)=>{const e=document.getElementById('hr-stack-h');e.value=v;e.dispatchEvent(new Event('change',{bubbles:true}))}",str(h[3]))
    await pg.evaluate("()=>document.querySelector('#hr-guide [data-go=villain]').click()")
    for i,v in enumerate(cs['vs']):
        await pg.evaluate("(s)=>document.querySelector('#hr-table [data-seat=\"'+s+'\"]').click()",v[0])
        await card(pg,v[1]);await card(pg,v[2])
        await pg.evaluate("([i,v])=>{const e=document.getElementById('hr-stack-v'+i);e.value=v;e.dispatchEvent(new Event('change',{bubbles:true}))}",[i+1,str(v[3])])
    await pg.evaluate("()=>document.querySelector('#hr-guide [data-go=play]').click()")
async def act(pg,a,board):
    while await pg.evaluate("()=>!document.getElementById('hr-deckbox').hidden"):await card(pg,board.pop(0))
    t=a.split(':')
    if t[0]=='raise':await pg.evaluate("(q)=>document.getElementById('hr-amt').value=q",t[1])
    return await pg.evaluate("(a)=>{const b=document.querySelector('#hr-recbody [data-act=\"'+a+'\"]');if(!b)return false;b.click();return true}",t[0])
async def main():
    srv=start_server();bad=[]
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':900})).new_page();errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8765/review/index.html');await asyncio.sleep(.5)
        for cs,exp in CASES:
            await setup(pg,cs);board=list(cs['board'])
            for a in cs['acts']:
                if not await act(pg,a,board):bad.append(f'버튼 없음 {a}');break
            while await pg.evaluate("()=>!document.getElementById('hr-deckbox').hidden") and board:await card(pg,board.pop(0))
            await pg.evaluate("()=>document.querySelector('#hr-guide [data-go=result]').click()")
            txt=await pg.evaluate("()=>document.getElementById('hr-story').innerText")
            for e in exp:
                if e not in txt:bad.append(f'결과에 "{e}" 없음: '+(re.search(r'쇼다운[^\n]*',txt) or [''])[0])
        # 최소 레이즈보다 작은 올인(2.2 오픈 → 3BB 올인) 뒤, 이미 액션한 오프너는 콜·폴드만
        await setup(pg,{"hero":["UTG","Ah","Kh",40],"vs":[["BTN","As","Kd",3],["BB","9c","9d",40]]});bd=[]
        for a in ["raise:2.2","raise:3","call"]:await act(pg,a,bd)
        acts=await pg.evaluate("()=>[...document.querySelectorAll('#hr-recbody [data-act]')].map(b=>b.dataset.act)")
        if 'raise' in acts or 'call' not in acts:bad.append(f'작은 올인 뒤 오프너 버튼 이상 {acts}')
        bad+=errs
    print('OK' if not bad else 'FAIL '+str(bad[:10]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
