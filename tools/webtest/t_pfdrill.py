# 오픈 연습 8~20BB 220개 상황 전부 그려 보기(NaN·점수) + 헤즈업 문제 해설이 헤즈업 계산을 쓰는지
import asyncio,sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from harness2 import *
async def main():
    srv=start_server()
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await b.new_page(viewport={'width':390,'height':844});pg.errs=[];pg.on('pageerror',lambda e:pg.errs.append(str(e)))
        await pg.goto('http://127.0.0.1:8765/index.html');await asyncio.sleep(1.5)
        r=await pg.evaluate("""()=>{const bad=[];let n=0;SCREEN='drill';
          for(const st of PFST){const P=DRILL_PF[st];const sps=[...DPOS.slice(0,8).map(p=>({kind:'pf',st,pos:p,spot:'rfi'})),...Object.keys(P.call).map(k=>{const[op,pos]=k.split('>');return{kind:'pf',st,pos,op,spot:'vs_shove'}})];
            for(const sp of sps){const f=pfF(sp),e=pfE(sp);if(!f||f.length!==169||!e||e.length!==169){bad.push('len '+JSON.stringify(sp));continue}
              f.forEach((x,i)=>{if(!(x>=0&&x<=1)||!isFinite(e[i]))bad.push('val '+sp.st+sp.spot+sp.pos+i)});
              // sign consistency: pure jam with negative EV
              let inc=0;f.forEach((x,i)=>{if((x>=.95&&e[i]<-0.05)||(x<=.05&&e[i]>0.05))inc++});if(inc)bad.push(`부호불일치 ${st}BB ${sp.spot} ${sp.op||''}>${sp.pos}: ${inc}`);
              const T=dTiers(sp);if(!T[1].length&&!T[2].length&&!T[3].length)bad.push('tier empty');
              for(const idx of [0,40,84,168,Math.floor(Math.random()*169)]){DS={sp,idx,hand:DH[idx],cards:dCards(idx),pick:null};drillRender();qTimerStop();const t1=document.getElementById('stage').innerText+document.getElementById('panel').innerText;
                drillAnswer(f[idx]>=.5?(sp.spot==='rfi'?'j':'c'):'f');const t2=document.getElementById('panel').innerText;n++;
                if(/NaN|undefined|null|\\[object/.test(t1+t2))bad.push('NaN '+JSON.stringify(sp)+idx);
                if(!/100점/.test(t2)&&Math.abs(f[idx]-0.5)>0.45)bad.push('점수 '+JSON.stringify(sp)+idx+' '+t2.slice(0,60))}}}
          // hand quiz: computed hands, answer vs chart reference
          const H=LEVELS[0].hands;const mm=[];
          H.forEach((h,hi)=>{const ref=chartRef(h);if(!ref||ref.sp.kind!=='pf')return;const i=clsIdx(h.hand);const fr=pfF(ref.sp)[i];const f=h.s[0].f;const go=ref.sp.spot==='rfi'?'jam':'call';
            if(f[go]==null)return;const ans=(+f[go]||0)/100;if(Math.abs(ans-fr)>=0.5)mm.push(`${h.me} vs ${h.vs} ${h.d}BB ${h.hand.join('')} 정답 ${go} ${f[go]}% / 참고차트 ${Math.round(fr*100)}% ${ref.exact?'(같은 스택)':'(가까운 '+ref.from+'BB)'} cv=${h.cv||0}`)});
          return {n,bad:bad.slice(0,30),nb:bad.length,mm}}""")
        print('연습 화면',r['n'],'개 그림, 문제',r['nb']);print('\n'.join(r['bad']))
        hu=[x for x in r['mm'] if x.startswith(('SB vs BB','BB vs SB')) and 'K♦8♣' not in x]
        print('핸드 정답 vs 참고 차트 차이(경계 핸드 참고용)',len(r['mm']));print('\n'.join(r['mm']))
        fail=r['nb']>0 or len(hu)>0 or [e for e in pg.errs if 'ERR_FAILED' not in e]
        print('FAIL' if fail else '이상 없음')
        print('errs',[e for e in pg.errs if 'ERR_FAILED' not in e][:5])
    srv.shutdown();sys.exit(1 if fail else 0)
asyncio.run(main())
