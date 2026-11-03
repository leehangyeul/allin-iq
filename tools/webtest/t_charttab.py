# 차트 탭: 모든 상황(RFI·vs 오픈·BB vs SB·푸시/폴드) × 스택 × 포지션을 눌러 보며 169칸 차트·범례·핸드 상세가 나오는지,
# 가로 넘침·NaN·undefined·오류가 없는지, 320·390·430 폭에서 확인해요.
import asyncio,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server();store['meta/season']={'v':0};bad=[];n=0
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await mkpage(b,{'anon':'u_x','google':{'uid':'g','email':ADMIN}})
        await pg.click('#admIn');await asyncio.sleep(1)
        for w in (320,390,430):
            await pg.set_viewport_size({'width':w,'height':844})
            await pg.evaluate("()=>{MENUTAB='home';menu();document.querySelector('.mnav [data-mt=\"chart\"]').click()}");await asyncio.sleep(.2)
            if not await pg.query_selector('#ctab'):bad.append(f'{w}px 차트 탭이 안 열림');continue
            r=await pg.evaluate("""async()=>{const out=[];const chk=(tag)=>{const el=document.getElementById('ctab');const t=el.innerText;
                const cells=el.querySelectorAll('.rg .rgc').length;const ov=document.documentElement.scrollWidth-document.documentElement.clientWidth;
                if(cells!==169&&!/차트가 없어요/.test(t))out.push(tag+' 칸 '+cells);if(ov>0)out.push(tag+' 가로 넘침 '+ov);if(/NaN|undefined|\\[object/.test(t))out.push(tag+' NaN/undefined');
                if(cells===169){el.querySelectorAll('.rg .rgc')[13*0+1].click();const d=document.getElementById('ctDet');if(!d||!/AKs/.test(d.innerText))out.push(tag+' 핸드 상세 없음');}};
              const click=(id,v)=>{const b=[...document.querySelectorAll('#'+id+' button')].find(x=>x.dataset.v===String(v));if(!b)return false;b.click();return true};
              let n=0;
              for(const mode of ['rfi','vso','bvs','pf']){click('ctMode',mode);
                const sts=[...document.querySelectorAll('#ctSt button')].map(b=>b.dataset.v);
                for(const st of sts){click('ctSt',st);
                  if(mode==='rfi'){for(const p of [...document.querySelectorAll('#ctPos button')].map(b=>b.dataset.v)){click('ctPos',p);chk(mode+' '+st+' '+p);n++}}
                  else if(mode==='vso'){for(const o of [...document.querySelectorAll('#ctOp button')].map(b=>b.dataset.v)){click('ctOp',o);
                    for(const d of [...document.querySelectorAll('#ctDef button')].map(b=>b.dataset.v)){click('ctDef',d);chk(mode+' '+st+' '+o+'>'+d);n++}}}
                  else if(mode==='bvs'){chk(mode+' '+st);n++}
                  else{click('ctPfk','jam');for(const p of [...document.querySelectorAll('#ctPos button')].map(b=>b.dataset.v)){click('ctPos',p);chk('pf jam '+st+' '+p);n++}
                    click('ctPfk','call');for(const o of [...document.querySelectorAll('#ctPop button')].map(b=>b.dataset.v)){click('ctPop',o);
                      for(const d of [...document.querySelectorAll('#ctDef button')].map(b=>b.dataset.v)){click('ctDef',d);chk('pf call '+st+' '+o+'>'+d);n++}}}}}
              // 100-75BB 표기와 믹스 안내
              click('ctMode','rfi');click('ctSt','75');const t=document.getElementById('ctab').innerText;
              if(!/100-75BB/.test(t))out.push('100-75BB 표기 없음');
              return{out,n}}""")
            bad+=[f'{w}px '+x for x in r['out']];n+=r['n']
        bad+=[e for e in pg.errs if 'ERR_FAILED' not in e]
    print(f'차트 화면 {n}개 확인');print('OK' if not bad else 'FAIL '+str(len(bad))+' '+str(bad[:10]));srv.shutdown();sys.exit(1 if bad else 0)
asyncio.run(main())
