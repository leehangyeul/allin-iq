const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const out={};
for(const [nm,f] of [["old","holdem-gto-quiz.html"],["new","chart1102/holdem-gto-quiz.html"]]){
 const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto('file://'+process.cwd()+'/'+f);await p.waitForTimeout(800);
 out[nm]=await p.evaluate(()=>{const r=[];LEVELS.forEach((L,li)=>L.hands.forEach((h,hi)=>{const s0=h.s[0];const keys=s0.o.map(x=>x[0]);
   const sorted=keys.slice().sort((a,b)=>(+s0.f[b]||0)-(+s0.f[a]||0));
   let cell=null;try{cell=typeof chartCell==="function"?chartCell(h):null}catch(e){}
   let ref=null;try{const x=chartRef(h);ref=x?x.sp.kind+":"+x.sp.st+":"+x.sp.spot:null}catch(e){ref="ERR "+e.message}
   r.push({id:li+"/"+hi,mult:!!h.multi,o:s0.o,me:h.me,vs:h.vs,d:h.d||100,hand:h.hand.join(""),top:sorted[0],sec:sorted[1],f:sorted.map(k=>k+":"+s0.f[k]).join(" "),n:s0.n,a:s0.a,cell:cell?cell.key+" "+cell.a+(cell.b||""):null,ref})}));return r});
 out[nm+"_err"]=errs;await p.close()}
require('fs').writeFileSync('cmp1102.json',JSON.stringify(out));
const O=out.old,N=out.new;let ch=0,mix=0,refs={old:0,new:0};const changed=[];
for(let i=0;i<O.length;i++){if(O[i].ref&&O[i].ref.startsWith("chart"))refs.old++;if(N[i].ref&&N[i].ref.startsWith("chart"))refs.new++;
 if(N[i].cell&&N[i].cell.split(" ")[1].length>1)mix++;
 if(O[i].top!==N[i].top){ch++;changed.push(N[i])}}
console.log("errors",out.old_err,out.new_err);console.log("hands",O.length,"top changed",ch,"mixed cells",mix,"chart refs",refs);
console.log("cells(new)",N.filter(x=>x.cell).length);
await b.close()})();
