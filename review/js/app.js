  // ---------- 핸드 복기 (테이블 · 멀티웨이 · 차트 · EV 표) ----------
  (function(){
    var RS="23456789TJQKA", SYM=["♠","♥","♦","♣"];
    var PRE=["UTG","UTG+1","UTG+2","LJ","HJ","CO","BTN","SB","BB"];
    var STN=["프리플랍","플랍","턴","리버"];
    function $(id){return document.getElementById(id)}
    function cTxt(c){return RS[c>>2]+SYM[c&3]}
    function isRed(c){return (c&3)===1||(c&3)===2}
    function pct(x){return (x*100).toFixed(1)+"%"}
    function bb(x){return (Math.round(x*10)/10)+"BB"}
    function sgn(x){return (x>=0?"+":"")+(Math.round(x*10)/10)+"BB"}

    // --- 7카드 평가기: 카드 c = 랭크(0=2 … 12=A)×4 + 무늬(0♠ 1♥ 2♦ 3♣)
    function sHigh(m){var x=(m<<1)|((m>>12)&1);for(var h=13;h>=4;h--){if(((x>>(h-4))&31)===31)return h-1}return -1}
    function enc(cat,a){var v=cat;for(var i=0;i<5;i++)v=v*16+(a[i]===undefined||a[i]<0?0:a[i]+1);return v}
    var CATU=1048576;
    function ev(cs){
      var rc=[0,0,0,0,0,0,0,0,0,0,0,0,0],sc=[0,0,0,0],sm=[0,0,0,0],rm=0,i,r;
      for(i=0;i<cs.length;i++){var c=cs[i],rr=c>>2,s=c&3;rc[rr]++;sc[s]++;sm[s]|=1<<rr;rm|=1<<rr}
      var f=-1;for(i=0;i<4;i++)if(sc[i]>=5)f=i;
      if(f>=0){var sf=sHigh(sm[f]);if(sf>=0)return enc(8,[sf])}
      var q=-1,t=[],p=[],s1=[];
      for(r=12;r>=0;r--){if(rc[r]===4)q=r;else if(rc[r]===3)t.push(r);else if(rc[r]===2)p.push(r);else if(rc[r]===1)s1.push(r)}
      if(q>=0){var k=-1;for(r=12;r>=0;r--)if(r!==q&&rc[r]>0){k=r;break}return enc(7,[q,k])}
      if(t.length&&(t.length>1||p.length))return enc(6,[t[0],Math.max(t.length>1?t[1]:-1,p.length?p[0]:-1)]);
      if(f>=0){var fl=[];for(r=12;r>=0&&fl.length<5;r--)if(sm[f]&(1<<r))fl.push(r);return enc(5,fl)}
      var st=sHigh(rm);if(st>=0)return enc(4,[st]);
      if(t.length)return enc(3,[t[0]].concat(s1.slice(0,2)));
      if(p.length>=2){var kk=-1;for(r=12;r>=0;r--)if(rc[r]>0&&r!==p[0]&&r!==p[1]){kk=r;break}return enc(2,[p[0],p[1],kk])}
      if(p.length===1)return enc(1,[p[0]].concat(s1.slice(0,3)));
      return enc(0,s1.slice(0,5));
    }
    function catOf(v){return Math.floor(v/CATU)}
    var CATN=["하이카드","원페어","투페어","트립스/셋","스트레이트","플러시","풀하우스","포카드","스트레이트 플러시"];

    // --- 레인지
    var IDX={};RG.classes.forEach(function(h,k){IDX[h]=k});
    function cls(a,b){var ra=a>>2,rb=b>>2;if(ra<rb){var x=ra;ra=rb;rb=x}var h=RS[ra]+RS[rb];return ra===rb?h:h+((a&3)===(b&3)?"s":"o")}
    function combosOf(h){var ra=RS.indexOf(h[0]),rb=RS.indexOf(h[1]),o=[],s,t;
      if(h.length===2){for(s=0;s<4;s++)for(t=s+1;t<4;t++)o.push([ra*4+s,ra*4+t])}
      else if(h[2]==="s"){for(s=0;s<4;s++)o.push([ra*4+s,rb*4+s])}
      else{for(s=0;s<4;s++)for(t=0;t<4;t++)if(s!==t)o.push([ra*4+s,rb*4+t])}
      return o}
    function rangeOf(str,W){var o=[];RG.classes.forEach(function(h,k){var w=W[str[k]]||0;if(w>0)combosOf(h).forEach(function(c){o.push({c:c,w:w})})});return o}
    var ORD=RG.classes.slice().sort(function(a,b){return D[b][0]-D[a][0]});
    function rangeTop(frac,skip){var o=[],acc=0;skip=skip||0;
      ORD.forEach(function(h){var n=h.length===2?6:(h[2]==="s"?4:12);if(acc>=skip*1326&&acc<frac*1326)combosOf(h).forEach(function(c){o.push({c:c,w:1})});acc+=n});return o}
    function rWeight(r){return r.reduce(function(s,o){return s+o.w},0)}

    // --- 승률: 나 vs 상대 여러 명(각자 레인지 또는 실제 카드)
    function pick(P){var x=Math.random()*P.tot,lo=0,hi=P.cum.length-1;while(lo<hi){var m=(lo+hi)>>1;if(P.cum[m]<x)lo=m+1;else hi=m}return P.list[lo].c}
    function prep(range,dead){var list=range.filter(function(o){return !dead[o.c[0]]&&!dead[o.c[1]]}),cum=[],tot=0;list.forEach(function(o){tot+=o.w;cum.push(tot)});return {list:list,cum:cum,tot:tot}}
    function eqMulti(hero,opps,board,iters){ // opps: [range | [c1,c2]]
      var dead={};hero.concat(board).forEach(function(c){dead[c]=1});
      var Ps=opps.map(function(o){return Array.isArray(o)&&typeof o[0]==="number"?prep([{c:o,w:1}],dead):prep(o,dead)});
      if(Ps.some(function(P){return !P.list.length}))return null;
      var win=0,n=0,guard=0;
      while(n<iters&&guard<iters*5){guard++;
        var used={},ok=true,hs=[];
        for(var i=0;i<Ps.length;i++){var c=pick(Ps[i]);if(used[c[0]]||used[c[1]]){ok=false;break}used[c[0]]=used[c[1]]=1;hs.push(c)}
        if(!ok)continue;
        var b=board.slice();while(b.length<5){var x=(Math.random()*52)|0;if(dead[x]||used[x])continue;used[x]=1;b.push(x)}
        var me=ev(hero.concat(b)),best=-1,tie=0;
        for(i=0;i<hs.length;i++){var v=ev(hs[i].concat(b));if(v>best){best=v;tie=1}else if(v===best)tie++}
        win+=me>best?1:(me===best?1/(tie+1):0);n++}
      return n?win/n:null}
    function rangeVsRange(A,B,board,iters){
      var dead={};board.forEach(function(c){dead[c]=1});var PA=prep(A,dead),PB=prep(B,dead);if(!PA.list.length||!PB.list.length)return null;
      var win=0,n=0,guard=0;
      while(n<iters&&guard<iters*4){guard++;var a=pick(PA),b2=pick(PB);if(a[0]===b2[0]||a[0]===b2[1]||a[1]===b2[0]||a[1]===b2[1])continue;
        var used={};used[a[0]]=used[a[1]]=used[b2[0]]=used[b2[1]]=1;var bd=board.slice();
        while(bd.length<5){var c=(Math.random()*52)|0;if(dead[c]||used[c])continue;used[c]=1;bd.push(c)}
        var x=ev(a.concat(bd)),y=ev(b2.concat(bd));win+=x>y?1:(x===y?0.5:0);n++}
      return n?win/n:null}
    function drawInfo(c2,board){var cs=c2.concat(board),sc=[0,0,0,0],rm=0,i;for(i=0;i<cs.length;i++){sc[cs[i]&3]++;rm|=1<<(cs[i]>>2)}
      var fd=false;for(i=0;i<4;i++)if(sc[i]===4&&((c2[0]&3)===i||(c2[1]&3)===i))fd=true;
      var outs=0;if(sHigh(rm)<0)for(var r=0;r<13;r++)if(!(rm&(1<<r))&&sHigh(rm|(1<<r))>=0)outs++;
      return {fd:fd,oe:outs>=2,gs:outs===1}}
    // 레인지에서 상위 keep 비율만 남기기(드로우는 남김). check는 최강 패 일부를 반으로.
    function narrowKeep(range,board,keep,mode){
      if(!board.length)return range;
      var dead={};board.forEach(function(c){dead[c]=1});
      var arr=range.filter(function(o){return !dead[o.c[0]]&&!dead[o.c[1]]}).map(function(o){
        var v=ev(o.c.concat(board)),d=drawInfo(o.c,board),ct=catOf(v),draw=(d.fd||d.oe)&&board.length<5,key=v;
        if(draw&&ct<=1)key=Math.max(key,1.55*CATU+(d.fd?2:0)+(d.oe?1:0));
        return {c:o.c,w:o.w,key:key,draw:draw}});
      arr.sort(function(a,b){return b.key-a.key});
      var tot=rWeight(arr),acc=0;
      arr.forEach(function(o){var fr=acc/tot;acc+=o.w;
        if(mode==="check"){if(fr<0.12)o.w*=0.5}
        else if(fr>keep){if(o.draw)o.w*=(mode==="raise")?0.5:1;else o.w=0}});
      return arr.filter(function(o){return o.w>0}).map(function(o){return {c:o.c,w:o.w}})}
    function keepFor(frac){return Math.max(0.3,Math.min(0.92,1/(1+frac)+0.08))} // 베팅이 팟의 frac일 때 계속하는 비율(MDF+조금)

    // ---------- 입력 상태 ----------
    var S={pl:[],card:{},active:null,acts:[],phase:"hero"}; // pl: {id,seat,stack} · phase: hero→villain→play
    var MAXV=5;
    function P(id){return S.pl.filter(function(p){return p.id===id})[0]}
    function nameOf(id){return id==="h"?"히어로":"빌런"+id.slice(1)}
    function gaOf(id){return id==="h"?"히어로가":nameOf(id)+("24".indexOf(id.slice(1))>=0||id.slice(1)==="5"?"가":"이")} // 빌런1·3 이 / 빌런2·4·5 가 (숫자 읽는 소리)
    function seatGa(s){return s+(s==="BTN"||s==="UTG+1"?"이":"가")}
    function cardsOf(id){var a=S.card[id+"1"],b=S.card[id+"2"];return a!==undefined&&b!==undefined?[a,b]:null}
    var SLOTNAME=function(k){if(k==="f1"||k==="f2"||k==="f3")return "플랍 "+k[1];if(k==="t")return "턴";if(k==="r")return "리버";return nameOf(k.slice(0,-1))+" 카드 "+k.slice(-1)};
    (function(){var h="";for(var s=0;s<4;s++)for(var r=12;r>=0;r--){var c=r*4+s;h+='<button type="button" class="hrc'+(isRed(c)?' red':'')+'" data-c="'+c+'" aria-label="'+cTxt(c)+'">'+RS[r]+'<br>'+SYM[s]+'</button>'}$("hr-deck").innerHTML=h})();

    // ---------- 베팅 엔진 (여러 명) ----------
    function blinds(){return {bbC:1,sb:0.5,ante:Math.max(0,+$("hr-ante").value||0)}}  // 모든 값은 BB 단위 (SB 0.5 · BB 1)
    function newGame(){
      var B=blinds(),G={st:0,pl:{},dead:B.ante,cur:1,minR:1,raises:0,raisers:[],callers:[],over:false,runout:false,toAct:null,lastAgg:null,preAgg:null};
      S.pl.forEach(function(p){G.pl[p.id]={id:p.id,seat:p.seat,live:p.stack/B.bbC-(p.seat==="BB"?B.ante:0),inv:0,sb:0,folded:false,allin:false,acted:false}});
      function seatP(s){for(var k in G.pl)if(G.pl[k].seat===s)return G.pl[k];return null}
      var sp=seatP("SB"),bp=seatP("BB");
      if(sp)put(G,sp,B.sb);else G.dead+=B.sb;
      if(bp)put(G,bp,1);else G.dead+=1;
      G.toAct=firstToAct(G);
      return G}
    function put(G,p,amt){var a=Math.max(0,Math.min(amt,p.live-p.inv));p.inv+=a;p.sb+=a;if(p.inv>=p.live-1e-9)p.allin=true;return a}
    function order(G){var ids=Object.keys(G.pl);var ref=G.st===0?PRE:["SB","BB","UTG","UTG+1","UTG+2","LJ","HJ","CO","BTN"];return ids.sort(function(a,b){return ref.indexOf(G.pl[a].seat)-ref.indexOf(G.pl[b].seat)})}
    function canAct(p){return !p.folded&&!p.allin}
    function needs(G,p){return canAct(p)&&(!p.acted||p.sb<G.cur-1e-9)}
    function firstToAct(G){var o=order(G);for(var i=0;i<o.length;i++)if(needs(G,G.pl[o[i]]))return o[i];return null}
    function nextAfter(G,id){var o=order(G),i=o.indexOf(id);for(var k=1;k<=o.length;k++){var q=G.pl[o[(i+k)%o.length]];if(needs(G,q))return q.id}return null}
    function alive(G){return Object.keys(G.pl).filter(function(k){return !G.pl[k].folded})}
    function pot(G){var s=G.dead;for(var k in G.pl)s+=G.pl[k].inv;return s}
    function streetPot(G){var s=pot(G);for(var k in G.pl)s-=G.pl[k].sb;return s}
    function toCall(G,p){return Math.max(0,Math.min(G.cur-p.sb,p.live-p.inv))}
    function apply(G,a){
      var p=G.pl[a.id];
      if(a.t==="fold")p.folded=true;
      else if(a.t==="call")put(G,p,toCall(G,p));
      else if(a.t==="raise"){var maxTo=p.sb+(p.live-p.inv),to=Math.min(Math.max(a.to,G.cur+G.minR),maxTo);if(a.to>=maxTo-1e-9)to=maxTo;
        if(to>G.cur+1e-9){G.minR=Math.max(G.minR,to-G.cur);G.cur=to;G.raises++;G.raisers.push(a.id);G.callers=[];G.lastAgg=a.id;if(G.st===0)G.preAgg=a.id;for(var k in G.pl)if(k!==a.id)G.pl[k].acted=false}
        put(G,p,to-p.sb)}
      if(a.t==="call")G.callers.push(a.id);
      p.acted=true;
      if(alive(G).length<=1){G.over=true;G.toAct=null;return}
      var nx=nextAfter(G,a.id);
      if(nx){G.toAct=nx;return}
      // 라운드 종료
      var actors=alive(G).filter(function(k){return !G.pl[k].allin});
      if(G.st===3){G.over=true;G.toAct=null;return}
      if(actors.length<=1){G.runout=true;G.toAct=null;return}
      G.st++;G.cur=0;G.minR=1;G.raises=0;G.raisers=[];G.callers=[];G.lastAgg=null;for(var k2 in G.pl){G.pl[k2].sb=0;G.pl[k2].acted=false}
      G.toAct=firstToAct(G)}
    function boardNeed(st){return st===1?["f1","f2","f3"]:st===2?["t"]:st===3?["r"]:[]}
    function boardReady(st){return boardNeed(st).every(function(k){return S.card[k]!==undefined})}
    function replay(){var G=newGame();for(var i=0;i<S.acts.length;i++)apply(G,S.acts[i]);return G}
    function actLabel(G,a,p){ // 기록·말풍선용 이름
      if(a.t==="fold")return "폴드";if(a.t==="check")return "체크";
      if(a.t==="call")return "콜 "+bb(toCall(G,p));
      var maxTo=p.sb+(p.live-p.inv),to=Math.min(Math.max(a.to,G.cur+G.minR),maxTo);if(a.to>=maxTo-1e-9)to=maxTo;
      var allin=to>=maxTo-1e-9,nm=G.st===0?(["오픈","3벳","4벳","5벳"][Math.min(G.raises,3)]):(G.cur===0?"벳":"레이즈");
      return (allin?"올인":nm)+" "+bb(to)}

    // ---------- 테이블 ----------
    function seatXY(seat,heroSeat,r){var i=PRE.indexOf(seat),h=PRE.indexOf(heroSeat),ang=(90+(i-h)*40)*Math.PI/180;return {x:50+Math.cos(ang)*r.x,y:50+Math.sin(ang)*r.y}}
    function cardEl(c,slot,on){
      if(slot){var has=c!==undefined;return '<button type="button" class="hrc'+(has?(isRed(c)?' red':''):' empty')+(on?' pick':'')+'" data-slot="'+slot+'" aria-label="'+SLOTNAME(slot)+'">'+(has?RS[c>>2]+'<br>'+SYM[c&3]:'+')+'</button>'}
      if(c===undefined||c===null)return '<span class="hrc back"></span>';
      return '<span class="hrc'+(isRed(c)?' red':'')+'">'+RS[c>>2]+'<br>'+SYM[c&3]+'</span>'}
    // st: {setup, heroSeat, seats:{id:seat}, stacks, bets, pot, board, cards, folded{id:1}, actor, say}
    function drawTable(st){
      var R={x:45,y:43},html='<div class="hr-felt"></div>',bySeat={};
      Object.keys(st.seats).forEach(function(id){bySeat[st.seats[id]]=id});
      var hs=st.heroSeat||"BTN";
      PRE.forEach(function(seat){
        var id=bySeat[seat],xy=seatXY(seat,hs,R);
        var cl="hr-seat"+(id==="h"?" hero":id?" villain":"")+(!id&&!st.setup?" dim":"")+(id&&st.folded&&st.folded[id]?" dim":"")+(id&&st.actor===id?" act":"")+(st.setup?" click":"");
        var tag=id?nameOf(id):(st.setup?"":"—");
        var stack=id&&st.stacks?bb(st.stacks[id]):"";
        var av=st.setup?'<button type="button" class="av" data-seat="'+seat+'" aria-label="'+seat+' 자리">'+seat+'</button>':'<div class="av">'+seat+'</div>';
        var say=(!st.setup&&st.say&&st.say.id===id&&id)?'<span class="hr-say '+(xy.x>50?'l':'r')+'">'+st.say.text+'</span>':'';
        html+='<div class="'+cl+'" style="left:'+xy.x+'%;top:'+xy.y+'%">'+av+(tag?'<span class="tag">'+tag+'</span>':'')+(stack?'<span class="st">'+stack+'</span>':'')+say+'</div>';
        if(id){var cx=seatXY(seat,hs,{x:30,y:24}),cards;
          if(st.setup)cards=cardEl(S.card[id+"1"],id+"1",S.active===id+"1")+cardEl(S.card[id+"2"],id+"2",S.active===id+"2");
          else{var cc=st.cards[id];cards=cc?cardEl(cc[0])+cardEl(cc[1]):cardEl(null)+cardEl(null)}
          if(st.setup||!(st.folded&&st.folded[id]))html+='<div class="hr-hole" style="left:'+cx.x+'%;top:'+cx.y+'%">'+cards+'</div>';
          var bx=seatXY(seat,hs,{x:20,y:16});
          if(!st.setup&&st.bets&&st.bets[id]>0)html+='<div class="hr-bet" style="left:'+bx.x+'%;top:'+bx.y+'%"><i></i>'+bb(st.bets[id])+'</div>';
        }
        if(seat==="BTN")html+='<div class="hr-dealer" style="left:'+(xy.x-7)+'%;top:'+(xy.y-7)+'%">D</div>';
      });
      var bd="";
      if(st.setup&&S.phase==="play")bd=["f1","f2","f3","t","r"].map(function(k){return cardEl(S.card[k],k,S.active===k)}).join("");
      else for(var i=0;i<5;i++)bd+=st.board&&st.board[i]!==undefined?cardEl(st.board[i]):'<span class="hrc empty" style="opacity:.35"></span>';
      html+='<div class="hr-board">'+bd+'</div>';
      if(!st.setup)html+='<div class="hr-pot">팟 '+bb(st.pot)+'</div>';
      $("hr-table").innerHTML=html}

    // ---------- 입력 화면: 게임하듯 단계별 진행 ----------
    // S.phase: hero(①) → villain(②) → play(③ 시작 후 ④~⑩). 핸드가 끝나면 '결과'.
    var STEPS=["히어로","빌런","시작","프리플랍 액션","플랍","플랍 액션","턴","턴 액션","리버","리버 액션","결과"];
    function hint(t,isErr){var h=$("hr-hint");h.textContent=t||"";h.className="hr-hint"+(isErr?" err":"")}
    function seatsMap(){var m={};S.pl.forEach(function(p){m[p.id]=p.seat});return m}
    function villains(){return S.pl.filter(function(p){return p.id!=="h"})}
    function stepIdx(G){
      if(S.phase==="hero")return 0;if(S.phase==="villain")return 1;
      if(!G)return 2;
      if(G.over||G.runout){var need=G.runout?[1,2,3].filter(function(s){return !boardReady(s)}):[];return need.length?[4,6,8][need[0]-1]:10}
      if(G.st===0)return 3;return boardReady(G.st)?[5,7,9][G.st-1]:[4,6,8][G.st-1]}
    function drawSetup(){
      var G=S.phase==="play"?replay():null,ended=G&&(G.over||G.runout),si=stepIdx(G);
      // 필요한 보드 카드는 카드판을 자동으로 열기
      if(G&&!S.active){var needSt=G.runout?[1,2,3].filter(function(s){return !boardReady(s)})[0]:(!G.over&&G.st>0&&!boardReady(G.st)?G.st:null);
        if(needSt&&!S.skipBoard)S.active=boardNeed(needSt).filter(function(k){return S.card[k]===undefined})[0]||null}
      drawTable({setup:true,heroSeat:P("h")?P("h").seat:"BTN",seats:seatsMap()});
      $("hr-steps").innerHTML=STEPS.map(function(n,i){return '<span class="'+(i<si?"done":i===si?"now":"")+'">'+(i<10?"①②③④⑤⑥⑦⑧⑨⑩"[i]+" ":"")+n+'</span>'}).join("");
      var used={};Object.keys(S.card).forEach(function(k){used[S.card[k]]=1});
      [].forEach.call($("hr-deck").querySelectorAll("button"),function(b){b.disabled=!!used[+b.dataset.c]&&S.card[S.active]!==+b.dataset.c});
      $("hr-deckbox").hidden=!S.active;
      if(S.active)$("hr-deckfor").textContent=SLOTNAME(S.active)+" 선택"+(S.active[0]==="v"?" (모르면 ‘닫기’)":"");
      // 플레이어·대회 정보는 시작 전에만
      $("hr-plbox").hidden=S.phase==="play";$("hr-info").hidden=S.phase==="play";$("hr-rec").hidden=S.phase!=="play";
      var rows=(S.phase==="hero"?S.pl.filter(function(p){return p.id==="h"}):S.pl);
      $("hr-plist").innerHTML=rows.length?rows.map(function(p){var c=cardsOf(p.id);return '<div class="hr-prow"><span class="nm">'+nameOf(p.id)+'<small>'+p.seat+'</small></span><label>스택(BB) <input type="number" min="1" step="0.5" id="hr-stack-'+p.id+'" data-id="'+p.id+'" value="'+p.stack+'" aria-label="'+nameOf(p.id)+' 스택(BB)"></label><span class="cards">'+(c?c.map(cTxt).join(" "):(p.id==="h"?"카드 미정":"카드 모름"))+'</span>'+(p.id!=="h"?'<button type="button" data-rm="'+p.id+'">빼기</button>':'<span></span>')+'</div>'}).join(""):'<div class="hr-cap">테이블에서 자리를 누르세요.</div>';
      var B=blinds();$("hr-infosum").textContent="BB 앤티 "+bb(B.ante)+" · 남은 "+$("hr-left").value+"명 / 입상권 "+$("hr-paid").value+"명";
      // 안내판
      var g="";
      if(S.phase==="hero"){
        if(!P("h"))g='<b>① 히어로 정하기</b><p>테이블에서 <b>내 자리</b>를 누르세요.</p>';
        else if(!cardsOf("h"))g='<b>① 히어로 정하기 · '+P("h").seat+'</b><p>아래 카드판에서 <b>내 카드 2장</b>을 고르세요. 자리를 바꾸려면 다른 자리를 누르면 됩니다.</p>';
        else g='<b>① 히어로 정하기 · '+P("h").seat+' '+cardsOf("h").map(cTxt).join("")+'</b><p>아래에서 <b>내 스택(BB)</b>을 확인하고 다음으로 넘어가세요.</p><div class="hr-btns"><button type="button" class="hr-go" data-go="villain">② 빌런 정하기 ▶</button></div>';
      } else if(S.phase==="villain"){
        var vs=villains();
        g='<b>② 빌런 정하기</b><p>테이블에서 <b>상대 자리</b>를 누르세요. 여러 명이면 계속 누르고(최대 '+MAXV+'명), 다시 누르면 빠집니다. 상대 카드는 알면 자리 앞 + 칸에 넣고, 모르면 비워 두세요. 스택은 아래 목록에서 BB로 정합니다.</p>'+
          (vs.length?'<p class="hr-cap">현재: '+vs.map(function(p){return nameOf(p.id)+' '+p.seat+' '+bb(p.stack)+(cardsOf(p.id)?' '+cardsOf(p.id).map(cTxt).join(""):'')}).join(" · ")+'</p>':'')+
          '<div class="hr-btns"><button type="button" class="hr-sub" data-go="hero">◀ 히어로 다시</button><button type="button" class="hr-go" data-go="play"'+(vs.length?'':' disabled')+'>③ 게임 시작 ▶</button></div>';
      } else if(ended){
        var needB=G.runout&&[1,2,3].some(function(s){return !boardReady(s)});
        var who=alive(G);
        g='<b>'+(needB?STEPS[si]+" 카드 넣기":"핸드 끝")+'</b><p>'+(who.length===1?gaOf(who[0])+" 팟 "+bb(pot(G))+"을 가져갔습니다.":needB?"올인으로 남은 액션이 없습니다. 남은 보드 카드를 넣으면 쇼다운 결과까지 해설합니다.":"쇼다운입니다. 팟 "+bb(pot(G))+".")+'</p>'+
          '<div class="hr-btns">'+(needB?'<button type="button" class="hr-sub" data-go="noboard">보드 없이 결과 보기</button>':'')+'<button type="button" class="hr-go" data-go="result">결과와 전체 해설 보기 ▶</button></div>';
      } else if(G.st>0&&!boardReady(G.st)){
        g='<b>'+"①②③④⑤⑥⑦⑧⑨⑩"[si]+' '+STN[G.st]+' 카드 넣기</b><p>'+(G.st===1?"플랍 카드 3장":G.st===2?"턴 카드 1장":"리버 카드 1장")+'을 아래 카드판에서 고르세요. 팟 '+bb(pot(G))+', 남은 인원 '+alive(G).length+'명.</p>';
      } else {
        var p=G.pl[G.toAct];
        g='<b>'+"①②③④⑤⑥⑦⑧⑨⑩"[si]+' '+STN[G.st]+' 액션</b><p><b>'+p.seat+' '+nameOf(p.id)+'</b> 차례입니다. 아래 버튼으로 이 사람이 실제로 한 액션을 누르세요. 라운드가 끝나면 다음 카드를 넣으라고 안내합니다.</p>';
      }
      $("hr-guide").innerHTML=g;
      // 액션 패널
      if(S.phase==="play"){
        var body="",log=[0,1,2,3].map(function(){return []}),Gx=newGame();
        S.acts.forEach(function(a){var q=Gx.pl[a.id];log[Gx.st].push('<span class="'+(a.id==="h"?'h':'')+'">'+q.seat+' '+nameOf(a.id)+' '+actLabel(Gx,a,q)+'</span>');apply(Gx,a)});
        var lg=log.map(function(l,i){return l.length?'<div><b>'+STN[i]+'</b>'+l.join("")+'</div>':''}).join("");
        if(!ended&&!(G.st>0&&!boardReady(G.st))){var p2=G.pl[G.toAct],tc=toCall(G,p2),pt=pot(G),maxTo=p2.sb+(p2.live-p2.inv);
          var def=G.st===0?(G.raises===0?2.2:Math.round(G.cur*3*10)/10):(G.cur===0?Math.round(pt*0.5*10)/10:Math.round(G.cur*3*10)/10);
          body='<div class="now">'+STN[G.st]+' · '+p2.seat+' '+nameOf(p2.id)+' 차례<small>팟 '+bb(pt)+(tc>0?' · 콜 '+bb(tc):'')+' · 남은 스택 '+bb(p2.live-p2.inv)+'</small></div>'+
            '<div class="hr-acts">'+(tc>0?'<button type="button" class="f" data-act="fold">폴드</button>':'')+(tc>0?'<button type="button" class="c" data-act="call">콜 '+bb(tc)+'</button>':'<button type="button" class="c" data-act="check">체크</button>')+
            (maxTo>G.cur+1e-9?'<button type="button" class="r" data-act="raise">'+(G.st===0?(G.raises===0?"오픈":(G.raises+2)+"벳"):(G.cur===0?"벳":"레이즈"))+'</button>':'')+'</div>'+
            (maxTo>G.cur+1e-9?'<div class="hr-size"><label for="hr-amt">크기(BB, 총액)</label><input id="hr-amt" type="number" step="0.1" min="0" value="'+Math.min(def,Math.round(maxTo*10)/10)+'">'+
              (G.st===0?[["2BB",2],["2.2BB",2.2],["2.5BB",2.5],["3배",G.cur*3],["올인",maxTo]]:[["33%",pt*0.33],["50%",pt*0.5],["75%",pt*0.75],["팟",pt],["3배",G.cur*3],["올인",maxTo]]).filter(function(x){return x[1]>G.cur+1e-9||x[0]==="올인"}).map(function(x){return '<button type="button" data-q="'+Math.min(Math.round((G.st===0||x[0]==="올인"||x[0]==="3배"?x[1]:x[1]+p2.sb)*10)/10,Math.round(maxTo*10)/10)+'">'+x[0]+'</button>'}).join("")+'</div>':'')}
        body+='<div class="hr-log">'+(lg||'<div class="hr-cap">프리플랍부터 차례대로 누르세요. 핸드에 없는 자리는 자동으로 폴드 처리됩니다.</div>')+'</div>'+
          (S.acts.length?'<div class="hr-tools"><button type="button" class="hr-sub" id="hr-undo">↶ 되돌리기</button></div>':'');
        $("hr-recbody").innerHTML=body}
    }
    function resetActs(msg){if(S.acts.length){S.acts=[];if(msg)setTimeout(function(){hint(msg,true)},0)}}
    $("hr-guide").addEventListener("click",function(e){var b=e.target.closest("[data-go]");if(!b||b.disabled)return;var go=b.dataset.go;hint("");
      if(go==="villain"){S.phase="villain";S.active=null}
      else if(go==="hero"){S.phase="hero";S.active=null}
      else if(go==="play"){if(!villains().length)return hint("빌런을 1명 이상 앉히세요",true);S.phase="play";S.active=null;S.skipBoard=false;S.acts=[]}
      else if(go==="noboard"){S.skipBoard=true;S.active=null;var r0=build();if(r0)return hint(r0,true);showTab("rv");return}
      else if(go==="result"){var r=build();if(r)return hint(r,true);showTab("rv");return}
      drawSetup()});
    $("hr-table").addEventListener("click",function(e){
      if($("hr-setup").hidden)return;
      var sb=e.target.closest("[data-seat]"),cb=e.target.closest("[data-slot]");
      if(sb){var seat=sb.dataset.seat,who=null;S.pl.forEach(function(p){if(p.seat===seat)who=p.id});
        if(S.phase==="hero"){if(who&&who!=="h")return;var h=P("h");if(h)h.seat=seat;else S.pl.push({id:"h",seat:seat,stack:40});if(!cardsOf("h"))S.active=S.card.h1===undefined?"h1":"h2"}
        else if(S.phase==="villain"){
          if(who==="h")return hint("히어로 자리입니다. 다른 자리를 누르세요",true);
          if(who){S.pl=S.pl.filter(function(p){return p.id!==who});delete S.card[who+"1"];delete S.card[who+"2"];S.active=null}
          else{if(villains().length>=MAXV)return hint("빌런은 최대 "+MAXV+"명까지입니다",true);
            var used2={};S.pl.forEach(function(p){used2[p.id]=1});var nid="v1";for(var k=1;k<=MAXV;k++)if(!used2["v"+k]){nid="v"+k;break}
            S.pl.push({id:nid,seat:seat,stack:50});S.active=nid+"1"}}
        else return hint("게임 중에는 자리를 바꿀 수 없습니다. 바꾸려면 ‘처음부터 다시’",true);
        hint("");drawSetup();return}
      if(cb){var sl=cb.dataset.slot;if(S.active===sl&&S.card[sl]!==undefined)delete S.card[sl];S.active=sl;drawSetup()}});
    var GROUP=function(k){if(/^(f[123]|t|r)$/.test(k))return ["f1","f2","f3","t","r"];var id=k.slice(0,-1);return [id+"1",id+"2"]};
    $("hr-deck").addEventListener("click",function(e){var b=e.target.closest("button");if(!b||b.disabled||!S.active)return;S.card[S.active]=+b.dataset.c;
      var g=GROUP(S.active),nx=null;for(var k=g.indexOf(S.active)+1;k<g.length;k++)if(S.card[g[k]]===undefined){nx=g[k];break}
      if(g[0]==="f1"){var G=S.phase==="play"?replay():null;var lim=G?(G.runout?3:Math.max(1,G.st)):1;if(nx&&["f1","f2","f3","t","r"].indexOf(nx)>=[3,4,5][lim-1])nx=null} // 지금 필요한 보드까지만
      S.active=nx;drawSetup()});
    $("hr-deckclose").addEventListener("click",function(){S.active=null;if(S.phase==="play")S.skipBoard=true;drawSetup();S.skipBoard=false});
    $("hr-recbody").addEventListener("click",function(e){
      var q=e.target.closest("[data-q]");if(q){$("hr-amt").value=q.dataset.q;return}
      if(e.target.id==="hr-undo"){S.acts.pop();drawSetup();return}
      var b=e.target.closest("[data-act]");if(!b)return;var G=replay();if(!G.toAct)return;
      var a={id:G.toAct,t:b.dataset.act};if(a.t==="raise"){a.to=+$("hr-amt").value;if(!(a.to>0))return}
      S.acts.push(a);drawSetup()});
    $("hr-plist").addEventListener("change",function(e){var id=e.target.dataset.id;if(!id)return;P(id).stack=+e.target.value;drawSetup()});
    $("hr-plist").addEventListener("click",function(e){var id=e.target.dataset.rm;if(!id)return;S.pl=S.pl.filter(function(p){return p.id!==id});delete S.card[id+"1"];delete S.card[id+"2"];drawSetup()});
    $("hr-ante").addEventListener("change",drawSetup);
    ["hr-left","hr-paid","hr-ft"].forEach(function(id){$(id).addEventListener("change",drawSetup)});
    $("hr-reset").addEventListener("click",function(){S={pl:[],card:{},active:null,acts:[],phase:"hero"};hint("");showTab("in")});
    function showTab(w){$("hr-tab-in").setAttribute("aria-selected",w==="in");$("hr-tab-rv").setAttribute("aria-selected",w==="rv");$("hr-setup").hidden=w!=="in";$("hr-replay").hidden=w!=="rv";if(w==="in"){$("hr-table").hidden=false;S.active=null;drawSetup()}else{showView("story");drawStep();drawStory()}}
    function showView(v){$("hr-v-story").setAttribute("aria-selected",v==="story");$("hr-v-step").setAttribute("aria-selected",v==="step");$("hr-story").hidden=v!=="story";$("hr-stepview").hidden=v!=="step";$("hr-table").hidden=v==="story";$("hr-sumbox").hidden=v==="story"}
    $("hr-v-story").addEventListener("click",function(){showView("story")});
    $("hr-v-step").addEventListener("click",function(){showView("step");drawStep()});
    $("hr-story").addEventListener("click",function(e){var b=e.target.closest("[data-k]");if(!b)return;cur=+b.dataset.k;showView("step");drawStep();$("hand-review").scrollIntoView({block:"start"})});
    $("hr-tab-in").addEventListener("click",function(){showTab("in")});
    $("hr-tab-rv").addEventListener("click",function(){var r=build();if(r){showTab("in");hint(r,true);return}showTab("rv")});

    // ---------- 평가 ----------
    function depthKey(x){return x>=87?"100":x>=57?"75":x>=35?"40":x>=25?"30":x>=17.5?"20":x>=12.5?"15":"10"}
    // ICM 리스크 프리미엄: 기준서(자료집 A)·GTO 홀덤 테이블과 같은 값 — 초·중반 0 / 머니 근처 +3 / 버블 +7 / 파이널 +4 (%p)
    function icmZone(L,Pd,ft){
      if(ft||L<=9)return {name:"파이널 테이블",prem:0.04,txt:"순위가 하나 오를 때마다 받는 몫이 크게 달라지는 구간입니다. 탈락하면 그 순위 점프를 놓치기 때문에, 올인 콜에는 칩EV 계산보다 약 4%p 높은 승률이 필요합니다(리스크 프리미엄)."};
      if(L>Pd&&L<=Pd*1.15)return {name:"버블",prem:0.07,txt:"입상권 바로 앞이라 ICM 압박이 가장 큽니다. 예를 들어 25BB에서 BTN 오픈에 BB 올인을 받으면 칩EV로는 약 44~46% 승률이면 콜이지만, 버블에서는 약 53%가 필요합니다(약 +7%p)."};
      if(L<=Pd)return {name:"입상권 안(순위 점프 구간)",prem:0.03,txt:"이미 입상권이지만 순위가 오를 때마다 몫이 커져 ICM이 조금 작용합니다. 기준서에 이 구간 값이 따로 없어 머니 근처와 같은 +3%p로 봅니다."};
      if(L<=Pd*1.5)return {name:"머니 근처",prem:0.03,txt:"입상권이 가까워지며 ICM 압박이 생기기 시작합니다. 올인 콜에 칩EV보다 약 3%p 높은 승률이 필요합니다."};
      return {name:"초·중반 (칩EV 구간)",prem:0,txt:"입상권까지 멀어 칩 개수 그대로(칩EV) 판단해도 되는 구간입니다. 근사 차트도 칩EV 기준입니다."}}
    function proxySeat(s){return s==="BB"||s==="BTN"?s:(s==="SB"?"BB":"BTN")}
    function defStr(d,def,op){if(!DEF.def[d])return null;var w=DEF.def[d][def]&&DEF.def[d][def][op]?def:proxySeat(def),s=DEF.def[d][w]&&DEF.def[d][w][op];return s?{s:s,proxy:w!==def,who:w}:null}
    function tbStr(kind,d,thr,op){if(!TB[kind][d])return null;var w=TB[kind][d][thr]&&TB[kind][d][thr][op]?thr:proxySeat(thr),s=TB[kind][d][w]&&TB[kind][d][w][op];return s?{s:s,proxy:w!==thr,who:w}:null}
    var CODEN={r:"오픈",m:"섞기·경계",".":"폴드",j:"잼(올인)",v:"레이즈(밸류)",b:"레이즈(블러프)",c:"콜"};
    function miniChart(str,hand,title,cap){
      var h='<div><div style="font-size:12.5px;font-weight:700;margin-bottom:4px">'+title+'</div><div class="hr-chart">';
      RG.classes.forEach(function(x,k){var c=str[k],col=COL[c]||COL["."];h+='<i class="'+(x===hand?'me':'')+'" style="background:'+col[0]+';color:'+col[1]+'">'+x+'</i>'});
      return h+'</div><div class="hr-cap">'+cap+'</div><div class="hr-cap">근사 차트: 오픈 대응·3벳·4벳은 ALLIN IQ 기준서 빈도(자리·스택별)에 맞춰 핸드 강도 순서로 채운 차트예요. 솔버 정답이 아니고, 칸마다 대표 행동 하나만 보여 줘요.</div></div>'}
    var W1={r:1,m:0.5},WJ={j:1,m:0.5},WV={v:1,b:1,j:1,m:0.5},WC={c:1,m:0.5};

    var TL=[],SUM="",cur=0;
    function build(){
      TL=[];cur=0;
      if(!P("h"))return "히어로 자리를 먼저 고르세요.";
      if(S.pl.length<2)return "빌런을 1명 이상 앉히세요.";
      if(!cardsOf("h"))return "히어로 카드 2장을 고르세요.";
      if(!S.acts.length)return "액션을 1개 이상 기록하세요.";
      var L=+$("hr-left").value,Pd=+$("hr-paid").value,zone=icmZone(L,Pd,$("hr-ft").checked),Bl=blinds();
      var G=newGame(),ids=Object.keys(G.pl),K={},H={},R={};
      ids.forEach(function(id){K[id]=cardsOf(id);H[id]=K[id]?cls(K[id][0],K[id][1]):null;R[id]=null});
      var board=[],shownSt=0,stStart={};ids.forEach(function(id){stStart[id]=G.pl[id].live});
      function seatOf(id){return G.pl[id].seat}
      function lives(){var o={};ids.forEach(function(id){o[id]=G.pl[id].live-G.pl[id].inv});return o}
      function bets(){var o={};ids.forEach(function(id){o[id]=G.pl[id].sb});return o}
      function folds(){var o={};ids.forEach(function(id){if(G.pl[id].folded)o[id]=1});return o}
      function step(label,id,say){TL.push({st:STN[G.st],label:label,id:id,say:say?{id:id,text:say}:null,ev:[]})}
      function done(){var e=TL[TL.length-1];e.bets=bets();e.pot=streetPot(G);e.stacks=lives();e.board=board.slice();e.folded=folds()}
      function add(id,vd,title,html,extra){TL[TL.length-1].ev.push({id:id,vd:vd,title:title,html:html,extra:extra||""})}
      function oppsOf(id){return alive(G).filter(function(k){return k!==id})}
      function effOf(id){var mine=G.pl[id].live,others=oppsOf(id).map(function(k){return G.pl[k].live});return Math.min(mine,others.length?Math.max.apply(null,others):mine)}
      function covered(id){return oppsOf(id).some(function(k){return G.pl[k].live>=G.pl[id].live})}
      function isIP(id){var o=["SB","BB","UTG","UTG+1","UTG+2","LJ","HJ","CO","BTN"];var me=o.indexOf(seatOf(id));return oppsOf(id).every(function(k){return o.indexOf(seatOf(k))<me})}
      function posTxt(id){return isIP(id)?"IP":"OOP"}
      function realize(id){if(G.st===3)return 1;var r=isIP(id)?0.97:0.85;return r-0.04*Math.max(0,oppsOf(id).length-1)}
      function rangeOr(id,fb){return R[id]||fb||rangeTop(0.3)}

      step("핸드 시작",null,null);
      add("h","info","핸드 시작","<p>"+S.pl.map(function(p){return p.seat+" "+nameOf(p.id)+" "+bb(G.pl[p.id].live)+(K[p.id]?" ("+K[p.id].map(cTxt).join("")+")":"")}).join(" · ")+"</p><p>토너먼트: <b>"+zone.name+"</b>. "+zone.txt+(zone.prem?" 올인 콜에는 필요 승률에 약 "+pct(zone.prem)+"를 더해 평가합니다(나를 커버하는 상대가 없으면 절반).":"")+"</p><p>블라인드 0.5BB/1BB, BB 앤티 "+bb(Bl.ante)+" → 시작 팟 "+bb(pot(G))+". 핸드에 없는 자리는 폴드로 봅니다.</p>");
      done();

      for(var ai=0;ai<S.acts.length;ai++){
        var a=S.acts[ai];if(G.over||G.runout||!G.toAct)break;
        if(a.id!==G.toAct)return "기록 순서가 맞지 않습니다. ‘처음부터 다시’를 눌러 다시 기록하세요.";
        // 새 스트리트 공개
        if(G.st>shownSt){
          if(!boardReady(G.st))break;
          for(var s2=shownSt+1;s2<=G.st;s2++){board=board.concat(boardNeed(s2).map(function(k){return S.card[k]}))}
          shownSt=G.st;
          step(board.slice(G.st===1?0:board.length-1).map(cTxt).join(" ")+" 공개",null,null);
          if(G.st===1&&G.preAgg&&!G.pl[G.preAgg].folded){var ag=G.preAgg,others=oppsOf(ag);
            var ra=rangeVsRange(rangeOr(ag),rangeOr(others[0]),board,1200);
            if(ra!==null)add(ag,"info","이 보드는 누구 편인가","<p>프리플랍 공격자 "+nameOf(ag)+"("+seatOf(ag)+")의 레인지가 "+nameOf(others[0])+" 레인지 상대로 "+pct(ra)+"의 승률입니다. "+(ra>=0.58?"공격자에게 크게 유리한 보드라 자주 c-bet합니다.":ra>=0.52?"공격자가 조금 유리해서 섞어서 c-bet합니다.":"콜러 쪽 보드라 공격자는 체크를 많이 섞습니다.")+(others.length>1?" 멀티웨이("+(others.length+1)+"명)에서는 누군가 맞았을 확률이 높아 c-bet 빈도와 블러프를 크게 줄입니다.":"")+"</p>")}
          done();
        }
        var p=G.pl[a.id],id=a.id,tc=toCall(G,p),ptNow=pot(G),label=actLabel(G,a,p),eff=effOf(id),d=depthKey(eff),dOpen=(d==="15"||d==="10")?"20":d,dTB=d==="10"?"15":d;
        step(seatOf(id)+" "+nameOf(id)+" "+label,id,label);
        var hand=H[id],known=!!K[id];
        var maxTo=p.sb+(p.live-p.inv),toAmt=a.t==="raise"?Math.min(Math.max(a.to,G.cur+G.minR),maxTo):0;if(a.t==="raise"&&a.to>=maxTo-1e-9)toAmt=maxTo;
        var isAllinAct=a.t==="raise"&&toAmt>=maxTo-1e-9;
        // ---------- 프리플랍 ----------
        if(G.st===0){
          var raises=G.raises,opener=G.raisers[0],callers=G.callers.slice(),seat=seatOf(id),newR=null;
          if(raises===0){
            var src=RG.open[dOpen][seat==="BB"?"SB":seat],jam=(d==="15"||d==="10")?RG.jam[d][seat==="BB"?"SB":seat]:null;
            if(a.t==="raise")newR=isAllinAct&&jam?rangeOf(jam,WJ):rangeOf(src,W1);else if(a.t==="call")newR=seat==="SB"?rangeOf(src,W1):rangeTop(0.35);else if(a.t==="check")newR=rangeTop(1,0.08);
            if(seat==="BB"&&callers.length===1&&seatOf(callers[0])==="SB"){ // SB 림프에 BB(IP) 대응
              var lc=DEF.limp[d];newR=a.t==="raise"?rangeOf(lc,{v:1,b:1,j:1,m:0.5}):rangeOf(lc,{".":1,m:0.5});
              if(known){var cl=lc[IDX[hand]],want0=(cl==="v"||cl==="b"||cl==="j")?"raise":cl==="m"?"mix":"check",vd0=a.t==="raise"?(want0==="raise"?"good":want0==="mix"?"mix":"bad"):(want0==="check"?"good":want0==="mix"?"mix":"mix");
                add(id,vd0,"SB 림프에 대응 (BB IP)","<p>SB가 림프했고 "+gaOf(id)+" BB에서 "+hand+"로 <b>"+(a.t==="raise"?"레이즈":"체크")+"</b>했습니다. BB는 플랍 이후 IP라 약 35%를 레이즈(밸류 + 오프수트 Kx·Qx 블러프)하고 나머지는 체크로 공짜 플랍을 봅니다. 이 패는 차트에서 <b>"+CODEN[cl]+"</b>입니다.</p>",miniChart(lc,hand,"근사 차트 · "+d+"BB · BB vs SB 림프","빨강 밸류 레이즈 · 금색 블러프 레이즈 · 빈칸 체크. 내 패 "+hand+" = <b>"+CODEN[cl]+"</b>."))}}
            if(known&&seat!=="BB"){var c=(jam&&isAllinAct?jam:src)[IDX[hand]],vd,tx;
              var limpers=callers.length;
              if(a.t==="raise"){vd=(c==="r"||c==="j")?"good":c==="m"?"mix":"bad";tx=hand+"는 이 자리 차트에서 ‘"+CODEN[c]+"’입니다. "+(vd==="good"?"오픈하는 것이 기본입니다.":vd==="mix"?"경계 핸드라 뒤 사람들이 타이트하면 오픈, 3벳을 자주 하면 폴드합니다.":"차트보다 넓은 오픈입니다. 이 자리에선 폴드가 기본입니다.")}
              else if(a.t==="fold"){vd=c==="."?"good":c==="m"?"mix":"bad";tx=hand+"는 차트에서 ‘"+CODEN[c]+"’입니다. "+(vd==="good"?"폴드가 맞습니다.":vd==="mix"?"경계 핸드라 폴드도 괜찮습니다.":"오픈할 수 있는 패를 접었습니다. 앞이 모두 폴드했을 때 이 패는 이익이 나는 오픈입니다.")}
              else{vd=seat==="SB"&&c!=="."?"good":"bad";tx=seat==="SB"?(c!=="."?"SB는 BB만 남았을 때 림프를 섞을 수 있습니다(진입 범위 안).":"SB 진입 범위 밖의 패입니다. 폴드가 기본입니다."):"오픈 림프는 하지 않습니다. 처음 들어갈 때는 레이즈 아니면 폴드입니다. 림프는 뒤 사람에게 싸게 들어올 기회를 주고, 주도권(베팅으로 팟을 가져올 기회)도 잃기 때문입니다."+(limpers?" 앞에 림퍼가 있으면 크게 아이솔레이트하거나 플랍이 잘 맞는 패로 따라 림프합니다.":"")}
              if((d==="15"||d==="10")&&a.t==="raise"&&!isAllinAct){var jc=RG.jam[d][seat][IDX[hand]];tx+=" 단, "+d+"BB는 잼/폴드가 기준선이고 이 패는 잼 차트에서 ‘"+CODEN[jc]+"’입니다.";if(vd==="good"&&jc!=="j")vd="mix"}
              if(d!=="15"&&d!=="10"&&isAllinAct&&eff>22){vd="bad";tx+=" 다만 "+bb(eff)+"에서 첫 진입 올인은 위험이 너무 큽니다. 작은 오픈(2~2.5BB)이 기본입니다. 같은 폴드 이익을 훨씬 적은 칩으로 노릴 수 있고, 강한 패에 걸렸을 때 잃는 양도 작기 때문입니다."}
              add(id,vd,"첫 진입 결정 ("+seat+", "+bb(eff)+")","<p>"+tx+"</p>",miniChart(jam&&isAllinAct?jam:src,hand,"근사 차트 · "+((jam&&isAllinAct)?d+"BB 잼":dOpen+"BB 오픈")+" · "+seat,"내 패 "+hand+" = <b>"+CODEN[c]+"</b>. "+(dOpen!==d&&!(jam&&isAllinAct)?"("+d+"BB는 잼/폴드 기준이라 20BB 오픈 차트로 대신 봤습니다.) ":"")+"첫 진입 차트는 공개 차트의 비율로 만든 근사 차트입니다(20~100BB 근사, 10·15BB는 푸시·폴드 직접 계산)."))}
          }
          else if(raises===1&&callers.length===0&&!G.pl[opener].allin){
            var ds=defStr(dOpen,seat,seatOf(opener));
            var opR=rangeOr(opener);
            if(a.t==="raise")newR=(function(){var t=tbStr("tb",dTB,seat,seatOf(opener));return t?rangeOf(t.s,WV):rangeTop(0.08)})();else if(a.t==="call")newR=ds?rangeOf(ds.s,WC):rangeTop(0.2);
            if(known&&ds){var cd=ds.s[IDX[hand]],vd2,want=(cd==="v"||cd==="b"||cd==="j")?"3벳":cd==="c"?"콜":cd==="m"?"섞기":"폴드";
              var mine=a.t==="raise"?"3벳":a.t==="call"?"콜":"폴드";
              vd2=(mine===want)?"good":(cd==="m")?"mix":(mine==="콜"&&want==="3벳")?"mix":(mine==="3벳"&&cd==="c")?"mix":"bad";
              var eqo=eqMulti(K[id],[opR],[],1500),potA=ptNow+tc,evCall=eqo!==null?eqo*realize(id)*potA-tc:null;
              var why={"3벳":(cd==="v"?"오프너 범위를 상대로 앞서는 밸류 3벳입니다. 팟을 키울수록 이득이고, 뒤 블라인드의 스퀴즈도 막습니다.":cd==="j"?"이 스택에선 3벳이 곧 올인(리쇼브)이며, 이 패는 리쇼브 범위입니다.":"블로커와 플레이성이 좋은 블러프 3벳 후보입니다. 4벳을 받으면 깔끔하게 접습니다."),"콜":"3벳하기엔 약하지만 가격"+(isIP(id)?"과 포지션(IP)":"")+" 덕분에 이어갈 가치가 있습니다.","폴드":"오프너 범위 대비 승률이 낮거나 도미네이트(같은 높은 카드에 더 좋은 키커) 위험이 커서 접는 것이 기본입니다.","섞기":"경계 핸드라 상대 성향(3벳에 잘 접는지, 4벳이 많은지)에 따라 고릅니다."}[want];
              var tx2="<p>"+seatGa(seatOf(opener))+" "+bb(G.cur)+"로 오픈했고, "+gaOf(id)+" "+seat+"("+posTxt(id)+")에서 "+hand+"로 <b>"+mine+"</b>했습니다. 근사 차트에서 이 패는 <b>"+CODEN[cd]+"</b>입니다. "+why+"</p>"+(eqo!==null?"<p>오프너 범위 상대 승률 "+pct(eqo)+" · 콜 필요 승률 "+pct(tc/potA)+(evCall!==null?" · 콜의 간이 EV "+sgn(evCall)+" (실현율 "+realize(id).toFixed(2)+" 반영, 이후 베팅은 제외)":"")+".</p>":"")+(seat==="SB"&&mine==="콜"?"<p>SB는 BB가 뒤에 남아 3인 팟의 가장 나쁜 자리가 되므로 콜보다 3벳 아니면 폴드가 기본입니다.</p>":"")+(ds.proxy?"<p class='hr-cap'>※ "+seat+" 전용 차트가 없어 "+ds.who+" 차트로 대신 봤습니다.</p>":"");
              add(id,vd2,"오픈에 대응 ("+seat+" "+posTxt(id)+" vs "+seatOf(opener)+")",tx2,miniChart(ds.s,hand,"근사 차트 · "+dOpen+"BB · "+seatOf(opener)+" 오픈 → "+ds.who+" 대응","빨강 3벳 밸류 · 금색 3벳 블러프 · 파랑 콜 · 연한 칸 섞기. 내 패 "+hand+" = <b>"+CODEN[cd]+"</b>."))}
          }
          else if(raises===1&&callers.length>=1&&!G.pl[opener].allin){
            var key=seatOf(opener)+"+"+seatOf(callers[0])+">"+seat,dm=d==="100"||d==="75"?"100":(d==="40"||d==="30")?"40":"20",mw=DEF.mw[dm]&&DEF.mw[dm][key];
            var oppR=[opener].concat(callers).map(function(k){return rangeOr(k)});
            if(a.t==="raise")newR=mw?rangeOf(mw,WV):rangeTop(0.06);else if(a.t==="call")newR=mw?rangeOf(mw,WC):rangeTop(0.15);
            if(known){var e3=eqMulti(K[id],oppR,[],1500),potA3=ptNow+tc,r3=realize(id),evC3=e3!==null?e3*r3*potA3-tc:null,code3=mw?mw[IDX[hand]]:null;
              var mine3=a.t==="raise"?"스퀴즈":a.t==="call"?"콜":"폴드",vd3;
              if(code3){var want3=(code3==="v"||code3==="b"||code3==="j")?"스퀴즈":code3==="c"?"콜":code3==="m"?"섞기":"폴드";
                // 플레이할지(콜·스퀴즈)와 폴드할지가 차트와 엇갈리면 실수, 콜과 스퀴즈 사이의 선택은 대안
                vd3=mine3===want3?"good":code3==="m"?"mix":(mine3==="폴드"||want3==="폴드")?"bad":"mix"}
              else vd3=evC3===null?"info":(a.t==="call"?(evC3>0.3?"good":evC3>-0.3?"mix":"bad"):a.t==="fold"?(evC3<-0.3?"good":evC3<0.3?"mix":"bad"):(e3>0.45?"good":"mix"));
              var tx3="<p>"+seatOf(opener)+" 오픈 + "+callers.map(seatOf).join("·")+" 콜 → "+gaOf(id)+" "+seat+"에서 "+hand+"로 <b>"+mine3+"</b>했습니다. 멀티웨이(상대 "+oppR.length+"명)에서는 수딧·페어처럼 크게 맞는 패가 좋아지고, 오프수트 하이카드는 약해집니다.</p><p>상대 전원 대비 승률 "+(e3!==null?pct(e3):"-")+" · 콜 필요 승률 "+pct(tc/potA3)+(evC3!==null?" · 콜의 간이 EV "+sgn(evC3)+" (멀티웨이 실현율 "+r3.toFixed(2)+")":"")+".</p>"+(code3?"<p>멀티웨이 근사 차트에서 이 패는 <b>"+CODEN[code3]+"</b>입니다. 스퀴즈는 콜러가 캡드라 잘 통하고, 블러프는 KTs·JTs·A5s처럼 멀티웨이로 콜당해도 되는 패가 좋습니다.</p>":"<p>이 조합의 멀티웨이 차트가 없어 승률과 가격으로 평가했습니다. 스퀴즈는 상위 약 "+(seat==="BB"?"9":"5")+"%의 강한 패와 블로커 블러프로 구성합니다.</p>");
              add(id,vd3,"멀티웨이 대응 ("+seat+" "+posTxt(id)+")",tx3,code3?miniChart(mw,hand,"근사 차트 · "+dm+"BB · "+key.replace(">"," → "),"빨강 스퀴즈 · 금색 블러프 · 파랑 콜. 내 패 "+hand+" = <b>"+CODEN[code3]+"</b>."):"")}
          }
          else if(raises===2&&id===opener&&!G.pl[G.raisers[1]].allin){
            var thr=G.raisers[1],fb=tbStr("fb",dTB,seatOf(thr),seat),thrR=rangeOr(thr);
            if(a.t==="raise")newR=fb?rangeOf(fb.s,{v:1,m:0.5}):rangeTop(0.04);else if(a.t==="call")newR=rangeOr(id).filter(function(x){var hh=cls(x.c[0],x.c[1]);return !(fb&&fb.s[IDX[hh]]==="v")&&D[hh][0]>=55});
            if(known){var e4=eqMulti(K[id],[thrR],[],1500),potA4=ptNow+tc,r4=realize(id),evC4=e4!==null?e4*r4*potA4-tc:null,c4=fb?fb.s[IDX[hand]]:".";
              var mine4=a.t==="raise"?"4벳":a.t==="call"?"콜":"폴드",vd4;
              if(mine4==="4벳")vd4=c4==="v"?"good":c4==="m"?"mix":"bad";
              else if(c4==="v")vd4="mix";
              else vd4=evC4===null?"info":(mine4==="콜"?(evC4>0.3?"good":evC4>-0.5?"mix":"bad"):(evC4<0?"good":evC4<0.5?"mix":"bad"));
              add(id,vd4,"3벳에 대응 ("+seat+" "+posTxt(id)+" vs "+seatOf(thr)+")","<p>"+seatOf(thr)+"의 3벳 "+bb(G.cur)+"에 "+gaOf(id)+" "+hand+"로 <b>"+mine4+"</b>했습니다. 4벳 차트에서 이 패는 <b>"+CODEN[c4]+"</b>입니다.</p><p>3벳 범위 상대 승률 "+(e4!==null?pct(e4):"-")+" · 콜 필요 승률 "+pct(tc/potA4)+(evC4!==null?" · 콜의 간이 EV "+sgn(evC4):"")+". "+(isIP(id)?"IP라 콜 후에도 에퀴티를 잘 실현합니다.":"OOP에서 3벳 팟을 콜하면 에퀴티 실현이 나빠 4벳 아니면 폴드에 가깝습니다. OOP는 플랍 이후 먼저 행동해 정보가 적어서, 같은 승률이라도 실제로 가져가는 몫이 줄어듭니다.")+(d==="40"?" 40BB에서는 4벳을 올인하지 않고 3벳의 약 2배(예: 6.3BB 3벳에 IP 12BB·OOP 13BB)로 하는 것이 기준입니다.":(d==="75"||d==="100")?" 75BB 이상에서는 4벳을 3벳의 2.5~2.75배(예: 9BB 3벳에 25BB)로 하는 것이 기준입니다.":"")+"</p>",fb?miniChart(fb.s,hand,"근사 차트 · "+dTB+"BB · "+seat+" 4벳 vs "+fb.who+" 3벳","빨강 4벳 · 연한 칸 섞기(블러프 포함) · 빈칸은 폴드 또는 콜. 내 패 "+hand+" = <b>"+CODEN[c4]+"</b>."):"")}
          }
          else{ // 3벳 앞 콜드 / 4벳 이상 / 올인에 대응
            var agg=G.raisers[G.raisers.length-1],aggR=rangeOr(agg,rangeTop(raises>=3?0.03:0.06)),facingAllin=G.pl[agg].allin||tc>=p.live-p.inv-1e-9;
            if(a.t==="raise")newR=rangeTop(0.03);else if(a.t==="call")newR=rangeTop(raises>=2?0.06:0.1);
            if(known&&a.t!=="raise"){var e5=eqMulti(K[id],oppsOf(id).map(function(k){return rangeOr(k)}),[],2000),potA5=ptNow+tc,need=tc/potA5,pr=facingAllin?zone.prem*(covered(id)?1:0.5):0,r5=facingAllin?1:realize(id),evC5=e5!==null?e5*r5*potA5-tc:null;
              var diff=e5!==null?e5*r5-(need+pr):0,vd5=e5===null?"info":a.t==="call"?(diff>=0.02?"good":diff>=-0.03?"mix":"bad"):(diff<=-0.02?"good":diff<=0.03?"mix":"bad");
              if(raises===2&&id!==opener&&a.t==="call"&&!facingAllin){vd5=vd5==="good"?"mix":vd5}
              add(id,vd5,(facingAllin?"올인에 ":"리레이즈에 ")+(a.t==="call"?"콜":"폴드"),"<p>"+gaOf(id)+" "+hand+"로 "+(a.t==="call"?"콜":"폴드")+"했습니다. 필요 승률 "+pct(need)+(pr?" + ICM "+pct(pr)+" = "+pct(need+pr):"")+", 상대 레인지 대비 승률 "+(e5!==null?pct(e5):"-")+(r5<1?" × 실현율 "+r5.toFixed(2):"")+".</p><p>"+(vd5==="good"?(a.t==="call"?"가격 대비 승률이 충분해 콜이 맞습니다.":"승률이 가격에 못 미쳐 접는 것이 맞습니다."):vd5==="mix"?"손익분기 근처라 상대 성향에 따라 갈립니다.":(a.t==="call"?"가격에 비해 승률이 모자랍니다.":"충분한 승률을 버렸습니다."))+(raises===2&&id!==opener?" 오픈+3벳 앞에서는 4벳 아니면 폴드가 기본이고, 콜드콜은 아주 딥한 BTN의 예외입니다. 두 사람의 강한 레인지 사이에 끼면 승률을 제대로 실현하기 어렵기 때문입니다.":"")+(pr?" ICM 구간이라 칩EV보다 높은 승률이 필요합니다. 탈락하면 앞으로 받을 몫을 함께 잃기 때문입니다.":"")+"</p>",evC5!==null?evTable([["폴드",0],["콜",evC5]],a.t==="call"?"콜":"폴드","즉시 EV (BB). 콜 EV = 승률"+(r5<1?"×실현율":"")+"×콜 후 팟 − 콜 금액"+(pr?" (ICM 프리미엄은 판정에만 반영)":"")):"")}
            if(known&&a.t==="raise"){var e6=eqMulti(K[id],[aggR],[],1500);add(id,e6!==null&&e6>=0.55?"good":"mix",(isAllinAct?"올인으로 받아침":"리레이즈"),"<p>"+gaOf(id)+" "+hand+"로 다시 레이즈했습니다. 상대 공격 범위 대비 승률 "+(e6!==null?pct(e6):"-")+". "+(e6!==null&&e6>=0.55?"상대 범위보다 앞서는 밸류 레이즈입니다.":"범위 대비 앞서지 않아 블러프 성격입니다. 상대가 충분히 접어야 이득입니다.")+"</p>")}
          }
          if(newR)R[id]=newR;
          if(R[id]===null&&a.t!=="fold")R[id]=rangeTop(0.3);
        }
        // ---------- 플랍 이후 ----------
        else if(known){
          var opps=oppsOf(id),oppR2=opps.map(function(k){return rangeOr(k)}),eAll=eqMulti(K[id],oppR2,board,1600),rr=realize(id),pt=ptNow,options=[],mineKey;
          var di=drawInfo(K[id],board),dr=(di.fd||di.oe)&&G.st<3,made=catOf(ev(K[id].concat(board)));
          function betEV(B){ // B: 이번에 더 넣는 칩
            var fr=B/pt,keep=keepFor(fr),cont=oppR2.map(function(r){return narrowKeep(r,board,keep,"call")}),pf=Math.pow(1-keep,opps.length);
            var eC=eqMulti(K[id],cont,board,900);if(eC===null)return null;
            var nCall=Math.max(1,Math.round(opps.length*keep));  // 계속하는 상대 수(기댓값)
            return pf*pt+(1-pf)*(eC*rr*(pt+B+B*nCall)-B)}
          if(eAll!==null){
            if(tc===0){
              options.push(["체크",eAll*rr*pt]);
              [[0.33,"벳 33%"],[0.66,"벳 66%"],[1,"벳 팟"]].forEach(function(x){var B=Math.min(pt*x[0],p.live-p.inv);var v=betEV(B);if(v!==null)options.push([x[1]+" ("+bb(B)+")",v])});
              if(p.live-p.inv<=pt*1.5){var vj=betEV(p.live-p.inv);if(vj!==null)options.push(["올인 ("+bb(p.live-p.inv)+")",vj])}
              mineKey=a.t==="check"?"체크":"내 선택";
              if(a.t==="raise"){var Bm=toAmt-p.sb,vm=betEV(Bm);if(vm!==null)options.push(["내 선택: 벳 "+bb(Bm)+" ("+Math.round(Bm/pt*100)+"%)",vm]);mineKey="내 선택: 벳 "+bb(Bm)+" ("+Math.round(Bm/pt*100)+"%)"}
            } else {
              var potA=pt+tc,evc=eAll*rr*potA-tc;
              options.push(["폴드",0]);options.push(["콜 ("+bb(tc)+")",evc]);
              function raiseEV(to){var add2=to-p.sb,fr=(to-G.cur)/(pt+tc),keep=Math.max(0.35,keepFor(fr)*0.75),cont=oppR2.map(function(r){return narrowKeep(r,board,keep,"raise")}),pf=Math.pow(1-keep,opps.length),eC=eqMulti(K[id],cont,board,900);if(eC===null)return null;return pf*pt+(1-pf)*(eC*rr*(pt+add2+(to-G.cur))-add2)}
              var r3x=Math.min(G.cur*3,maxTo),v3=raiseEV(r3x);if(v3!==null)options.push(["레이즈 3배 ("+bb(r3x)+")",v3]);
              if(maxTo>r3x+1e-9){var vj2=raiseEV(maxTo);if(vj2!==null)options.push(["올인 ("+bb(maxTo)+")",vj2])}
              mineKey=a.t==="fold"?"폴드":a.t==="call"?"콜 ("+bb(tc)+")":null;
              if(a.t==="raise"){var vr=raiseEV(toAmt);if(vr!==null){var nm="내 선택: 레이즈 "+bb(toAmt);options.push([nm,vr]);mineKey=nm}}
            }
            var best=options.reduce(function(m,o){return o[1]>m[1]?o:m},options[0]),mineV=(options.filter(function(o){return o[0]===mineKey})[0]||[null,null])[1];
            var gap=mineV===null?0:best[1]-mineV,tol=Math.max(0.6,0.1*pt),mixTol=Math.max(1.5,0.25*pt),vdP=mineV===null?"info":gap<=tol?"good":gap<=mixTol?"mix":"bad";
            var checkToAgg=a.t==="check"&&!isIP(id)&&G.preAgg&&G.preAgg!==id&&!G.pl[G.preAgg].folded&&G.st===1;
            if(checkToAgg&&gap<=mixTol)vdP="good";  // 콜러가 플랍에서 공격자에게 체크하는 것은 기본
            // 상황 설명
            var kind=made>=4?"넛급 완성 패":made>=2?"강한 완성 패":made===1?"원페어":"하이카드";
            var role=eAll>=0.6?"밸류":eAll>=0.4?"쇼다운 가치가 있는 중간 패":dr?"드로우":"약한 패(블러프 후보)";
            var txt="<p>"+STN[G.st]+" · 팟 "+bb(pt)+(tc>0?" · 콜 금액 "+bb(tc)+" (필요 승률 "+pct(tc/(pt+tc))+")":"")+" · "+gaOf(id)+" "+posTxt(id)+" · 상대 "+opps.length+"명.</p>";
            txt+="<p>"+hand+"는 지금 <b>"+CATN[made]+"</b>"+(dr?" + "+(di.fd?"플러시 드로우":"")+(di.fd&&di.oe?"·":"")+(di.oe?"양쪽 스트레이트 드로우":""):"")+"이고, 상대 레인지 전체 대비 승률은 <b>"+pct(eAll)+"</b>("+role+")입니다. 실현율 "+rr.toFixed(2)+"("+(G.st===3?"리버":posTxt(id)==="IP"?"IP":"OOP")+(opps.length>1?", 멀티웨이 감점":"")+")를 반영했습니다.</p>";
            txt+="<p>EV 표에서 가장 높은 선택은 <b>"+best[0]+"</b>("+sgn(best[1])+")"+(mineV!==null?", 내 선택은 "+sgn(mineV)+"로 차이 "+(gap>0?bb(gap):"없음")+"입니다. ":". ")+
              (vdP==="good"?"가장 좋은 선택과 거의 같은 EV라 좋은 결정입니다.":vdP==="mix"?"조금 손해지만 상대 성향에 따라 충분히 고를 수 있는 선택입니다.":vdP==="bad"?"EV 차이가 커서 다른 선택이 확실히 낫습니다.":"")+"</p>";
            if(a.t==="raise"&&tc===0){var need2=(toAmt-p.sb)/(pt+toAmt-p.sb);txt+="<p>베팅이 바로 이득이려면 상대가 "+pct(need2)+" 이상 접어야 합니다(블러프 손익분기). 상대의 최소 방어 빈도(MDF)는 "+pct(1-need2)+"입니다. MDF는 1 − 베팅 ÷ (팟 + 베팅)으로, 상대가 이보다 자주 접으면 내 블러프가 바로 이득이 됩니다. "+(eAll>=0.6?"밸류 베팅은 더 약한 패에게 콜받을 때 이득이므로, 콜받을 패가 많은 보드에서는 크게, 넛이 적으면 작게 겁니다.":dr?"드로우는 세미블러프로 폴드 에퀴티와 완성 확률을 함께 가져갑니다.":"쇼다운으로 이기기 어려운 패의 블러프는 밸류 패 수와 균형을 맞추고, 상대 강한 패를 막는 블로커(상대의 강한 패를 만드는 카드를 내가 쥐고 있는 것)가 있을 때 좋습니다.")+(opps.length>1?" 멀티웨이에서는 블러프가 잘 통하지 않습니다.":"")+(!isIP(id)&&G.lastAgg!==id&&G.preAgg!==id?" 공격자에게 먼저 거는 리드(동크)는 보드가 내 레인지 쪽으로 바뀔 때만 작게 하는 것이 원칙입니다. 보통은 프리플랍 공격자의 레인지가 더 강하기 때문입니다.":"")+"</p>"}
            if(a.t==="call"&&tc>0)txt+="<p>"+(G.st===3?"리버 콜은 블러프 캐치입니다. 상대가 드로우를 놓친 보드에서 블러프를 많이 하는 타입이면 넓게, 블러프가 적은 니트면 좁게 콜합니다.":"턴·리버에서 더 큰 베팅을 받을 수 있어 실현율을 낮게 잡았습니다. 드로우는 완성되면 더 벌 수 있는 임플라이드 오즈(완성됐을 때 뒤에서 더 받을 수 있는 칩)가 있습니다.")+"</p>";
            if(checkToAgg)txt+="<p>프리플랍에서 콜한 쪽은 플랍에서 공격자에게 먼저 베팅(동크)하지 않고 체크하는 것이 기본입니다. 공격자의 레인지가 더 강하고, 체크한 뒤 체크레이즈로 반격할 수 있기 때문입니다. 간이 EV 표는 이런 이후 대응을 다 반영하지 못합니다.</p>";
            if(a.t==="check"&&tc===0&&eAll>=0.75)txt+="<p>"+(isIP(id)&&G.st===3?"리버에서 IP로 이렇게 강한 패를 체크백하면 밸류를 놓칩니다.":"강한 패의 체크는 슬로우플레이입니다. 드로우가 많은 보드에서는 공짜 카드를 주는 위험이 있습니다.")+"</p>";
            add(id,vdP,STN[G.st]+" 결정 ("+posTxt(id)+", 상대 "+opps.length+"명)",txt,evTable(options,mineKey,"간이 EV (BB, 솔버 아님): 체크 = 승률×실현율×팟. 벳·레이즈 = 상대가 모두 접을 확률×팟 + 그 밖엔 계속하는 범위 상대 승률로 계산. 상대가 계속하는 비율은 베팅 크기에 따라 MDF보다 조금 높게 둠."))
          }
        }
        // 레인지 좁히기 (플랍 이후)
        if(G.st>0){var fr2=a.t==="raise"?(toAmt-p.sb)/Math.max(ptNow,0.5):(tc/Math.max(ptNow,0.5));
          if(a.t==="raise")R[id]=narrowKeep(rangeOr(id),board,G.cur>0?0.3:(G.st===3?0.4:0.55),G.cur>0?"raise":"bet");  // 리버 베팅은 더 강한 범위
          else if(a.t==="call")R[id]=narrowKeep(rangeOr(id),board,keepFor(fr2),"call");
          else if(a.t==="check")R[id]=narrowKeep(rangeOr(id),board,1,"check")}
        apply(G,a);done();
      }
      // 남은 보드
      for(var s3=shownSt+1;s3<=3;s3++){if(!boardReady(s3))break;if(G.runout||G.over&&alive(G).length>1||s3<=G.st){board=board.concat(boardNeed(s3).map(function(k){return S.card[k]}));step(boardNeed(s3).map(function(k){return cTxt(S.card[k])}).join(" ")+" 공개",null,null);done()}}
      // 결과
      var live=alive(G),potEnd=pot(G),res;
      if(live.length===1)res=gaOf(live[0])+" 팟 "+bb(potEnd)+" 획득";
      else{var known2=live.filter(function(k){return K[k]});
        if(board.length===5&&known2.length===live.length){var sc=live.map(function(k){return [k,ev(K[k].concat(board))]}).sort(function(x,y){return y[1]-x[1]});res="쇼다운: "+sc.map(function(x){return nameOf(x[0])+" "+CATN[catOf(x[1])]}).join(" · ")+" → "+(sc.length>1&&sc[0][1]===sc[1][1]?"찹":nameOf(sc[0][0])+" 승")+" (팟 "+bb(potEnd)+")"}
        else res="쇼다운 (팟 "+bb(potEnd)+")"+(known2.length<live.length?" · 모르는 카드가 있어 승자는 표시하지 않습니다":"")}
      step(res,live.length===1?live[0]:null,null);
      var cnt={},worst=[];TL.forEach(function(e){e.ev.forEach(function(it){if(it.vd==="info")return;cnt[it.id]=cnt[it.id]||{good:0,mix:0,bad:0};cnt[it.id][it.vd]++;if(it.vd==="bad")worst.push(nameOf(it.id)+" · "+e.st+" "+e.label)})});
      add("h","info","복기 요약","<p>결과보다 결정을 보세요. "+(worst.length?"개선이 필요한 결정: "+worst.join(" / ")+".":"개선이 필요한 결정은 없었습니다.")+"</p>"+(ids.some(function(k){return k!=="h"&&!K[k]})?"<p>카드를 모르는 빌런의 결정은 평가하지 않았습니다. 카드를 넣으면 그 빌런도 평가합니다.</p>":""));
      done();
      var seats=seatsMap(),cardsAll={};ids.forEach(function(k){cardsAll[k]=K[k]});
      TL.forEach(function(e){e.seats=seats;e.cards=cardsAll;e.heroSeat=seats.h});
      SUM=Object.keys(cnt).map(function(k){var c=cnt[k];return '<span><b>'+nameOf(k)+'</b> <span style="color:var(--felt)">좋음 '+c.good+'</span> · <span style="color:var(--gold)">경계 '+c.mix+'</span> · <span style="color:var(--chip)">개선 '+c.bad+'</span></span>'}).join(" &nbsp; ");
      SUM='<div class="score">'+(SUM||"평가된 결정이 없습니다.")+'</div><div style="font-size:12.5px;color:var(--muted);margin-top:6px">승률은 몬테카를로 추정이라 다시 계산하면 1~2%p, EV는 조금 더 달라질 수 있습니다. 상대 레인지는 근사 차트에서 시작해 액션마다 좁힌 근사입니다(벳: 플랍·턴 상위 55%·리버 상위 40% + 드로우, 콜: 베팅 크기에 따른 MDF보다 조금 넓게, 레이즈: 상위 30%). 실현율은 리버 1.0, 그 전 IP 0.97·OOP 0.85(멀티웨이는 상대 1명당 −0.04). 간이 EV는 이후 스트리트의 베팅을 반영하지 못하므로, 판정은 EV 차이가 팟의 10% 이내면 ‘좋음’, 25% 이내면 ‘상황에 따라’로 넉넉하게 잡았습니다. 실제 솔버 결과와 다를 수 있습니다.</div>';
      return null;
    }
    function evTable(rows,mineKey,cap){
      if(!rows.length)return "";var best=rows.reduce(function(m,o){return o[1]>m[1]?o:m},rows[0]);
      return '<div><div style="font-size:12.5px;font-weight:700;margin-bottom:4px">액션별 EV</div><table class="hr-evt"><tbody>'+rows.map(function(r){return '<tr class="'+(r===best?'best ':'')+(r[0]===mineKey?'me':'')+'"><td>'+r[0]+(r===best?'<span class="tagb">최고</span>':'')+(r[0]===mineKey?'<span class="tagm">내 선택</span>':'')+'</td><td class="num">'+sgn(r[1])+'</td></tr>'}).join("")+'</tbody></table><div class="hr-cap">'+cap+'</div></div>'}
    function worstOf(e){var o={bad:3,mix:2,good:1},w=null;e.ev.forEach(function(it){if(o[it.vd]&&(!w||o[it.vd]>o[w]))w=it.vd});return w}
    // 전체 해설: 처음부터 리버까지 스트리트별로 한 번에 읽기
    function drawStory(){
      if(!TL.length){$("hr-story").innerHTML="";return}
      var VD={good:"좋은 결정",mix:"상황에 따라",bad:"개선 필요",info:"참고"},groups=[],g=null,last=TL[TL.length-1];
      TL.forEach(function(e,k){if(k===TL.length-1)return;if(!g||g.st!==e.st){g={st:e.st,items:[]};groups.push(g)}g.items.push([e,k])});
      function tot(e){var s=e.pot||0;for(var k in e.bets)s+=e.bets[k];return s} // 그 시점까지 들어간 전체 팟
      function item(it){return '<div class="hr-item '+it.vd+'"><div class="top"><span class="who'+(it.id!=="h"?" v":"")+'">'+nameOf(it.id)+'</span><span class="vd">'+VD[it.vd]+'</span><b>'+it.title+'</b></div><div class="hr-detail">'+it.html+'</div>'+(it.extra?'<details class="hr-more"><summary>근사 차트 · EV 표 보기</summary><div class="hr-two">'+it.extra+'</div></details>':'')+'</div>'}
      var h='<div class="hr-sumbox"><b>한눈에 보기</b>'+SUM+(last.ev[0]?'<div class="hr-detail" style="margin-top:8px">'+last.ev[0].html+'</div>':'')+'</div>';
      groups.forEach(function(gr){
        var e0=gr.items[0][0],eN=gr.items[gr.items.length-1][0],bd=eN.board||[];
        var inHand=Object.keys(e0.seats).filter(function(id){return !(e0.folded&&e0.folded[id])});
        h+='<section class="hr-sst"><div class="hd"><b>'+gr.st+'</b>'+(bd.length?'<span class="bd">'+bd.map(function(c){return cardEl(c)}).join("")+'</span>':'')+'<small>시작 팟 '+bb(tot(e0))+' · '+inHand.length+'명 · '+inHand.map(function(id){return e0.seats[id]+" "+nameOf(id)}).join(", ")+'</small></div>';
        gr.items.forEach(function(x){var e=x[0],k=x[1];
          h+='<div class="hr-sline'+(e.id==="h"?" h":"")+'"><button type="button" class="hr-sub" data-k="'+k+'" title="테이블에서 보기">▶ '+(k+1)+'</button><span>'+e.label+'</span>'+(e.id?'<small>→ 팟 '+bb(tot(e))+'</small>':'')+'</div>';
          if(e.ev.length)h+=e.ev.map(item).join("");
          else if(e.id&&!e.cards[e.id])h+='<div class="hr-snote">'+nameOf(e.id)+'의 카드를 몰라 이 결정은 평가하지 않았습니다. 이 액션 뒤로 '+nameOf(e.id)+'의 레인지를 좁혀서 히어로 평가에 씁니다.</div>'});
        h+='</section>'});
      h+='<section class="hr-sst end"><div class="hd"><b>결과</b></div><div class="hr-sline"><button type="button" class="hr-sub" data-k="'+(TL.length-1)+'">▶ '+TL.length+'</button><span>'+last.label+'</span></div></section>';
      $("hr-story").innerHTML=h}
    function drawStep(){
      if(!TL.length)return;var e=TL[cur];
      drawTable({setup:false,heroSeat:e.heroSeat,seats:e.seats,stacks:e.stacks,bets:e.bets,pot:e.pot,board:e.board,cards:e.cards,folded:e.folded,actor:e.id,say:e.say});
      $("hr-stepname").innerHTML=(cur+1)+" / "+TL.length+" · "+e.st+"<small>"+e.label+"</small>";
      $("hr-prev").disabled=cur===0;$("hr-next").disabled=cur===TL.length-1;
      $("hr-dots").innerHTML=TL.map(function(x,k){var w=worstOf(x);return '<button type="button" class="'+(w||"")+(k===cur?" cur":"")+'" data-k="'+k+'" aria-label="'+(k+1)+'단계"></button>'}).join("");
      var VD={good:"좋은 결정",mix:"상황에 따라",bad:"개선 필요",info:"참고"};
      $("hr-evals").innerHTML=e.ev.length?e.ev.map(function(it){return '<div class="hr-item '+it.vd+'"><div class="top"><span class="who'+(it.id!=="h"?" v":"")+'">'+nameOf(it.id)+'</span><span class="vd">'+VD[it.vd]+'</span><b>'+it.title+'</b></div>'+(it.extra?'<div class="hr-two">'+it.extra+'<div class="hr-detail">'+it.html+'</div></div>':'<div class="hr-detail">'+it.html+'</div>')+'</div>'}).join(""):
        '<div class="hr-none">'+(e.id&&!e.cards[e.id]?nameOf(e.id)+"의 카드를 모르면 결정을 평가하지 않습니다. 다음으로 넘어가세요.":"이 단계는 평가할 결정이 없습니다. 다음으로 넘어가세요.")+'</div>';
      $("hr-sumbox").innerHTML=SUM}
    $("hr-prev").addEventListener("click",function(){if(cur>0){cur--;drawStep()}});
    $("hr-next").addEventListener("click",function(){if(cur<TL.length-1){cur++;drawStep()}});
    $("hr-dots").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;cur=+b.dataset.k;drawStep()});
    $("hand-review").addEventListener("keydown",function(e){if($("hr-replay").hidden||e.target.tagName==="INPUT")return;if(e.key==="ArrowRight")$("hr-next").click();else if(e.key==="ArrowLeft")$("hr-prev").click()});
    $("hr-ex").addEventListener("click",function(){
      $("hr-left").value=300;$("hr-paid").value=135;$("hr-ft").checked=false;$("hr-ante").value=1;
      S={pl:[{id:"h",seat:"BTN",stack:40},{id:"v1",seat:"CO",stack:35},{id:"v2",seat:"BB",stack:50}],card:{h1:45,h2:41,v21:39,v22:35,f1:42,f2:31,f3:8,t:1,r:26},active:null,phase:"play",
        acts:[{id:"v1",t:"raise",to:2.2},{id:"h",t:"call"},{id:"v2",t:"call"},
              {id:"v2",t:"check"},{id:"v1",t:"check"},{id:"h",t:"raise",to:3.5},{id:"v2",t:"call"},{id:"v1",t:"fold"},
              {id:"v2",t:"check"},{id:"h",t:"raise",to:8},{id:"v2",t:"call"},
              {id:"v2",t:"raise",to:14},{id:"h",t:"call"}]};
      var r=build();if(r){showTab("in");hint(r,true);return}showTab("rv")});
    drawSetup();
  })();
