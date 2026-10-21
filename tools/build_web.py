# builds webapp/index.html from the claude.ai game file: same game, Firebase data layer, PWA shell
import re,json,datetime,sys,os
# usage: python3 tools/build_web.py <game source html> [<site folder, default: repo root>]
SRC=sys.argv[1] if len(sys.argv)>1 else 'holdem-gto-quiz.html'
SITE=sys.argv[2] if len(sys.argv)>2 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(SITE,'index.html')
s=open(SRC,encoding='utf8').read()
def rep(o,n,cnt=1):
    global s
    assert s.count(o)==cnt,(s.count(o),o[:80]);s=s.replace(o,n)
VER=datetime.datetime.now().strftime('%Y%m%d%H%M')
# fonts: real files instead of the inline subset
s,n=re.subn(r'src:url\(data:font/woff;base64,[A-Za-z0-9+/=]+\) format\("woff"\)',lambda m:'',s)
assert n==4
for w,f in [("400","Regular"),("600","SemiBold"),("700","Bold"),("800","ExtraBold")]:
    rep(f'@font-face{{font-family:"Pretendard";font-weight:{w};font-display:swap;}}',f'@font-face{{font-family:"Pretendard";font-weight:{w};font-display:swap;src:url("fonts/Pretendard-{f}.woff2") format("woff2")}}')
rep('/* Pretendard (SIL OFL 1.1), subset to the glyphs this page uses */','/* Pretendard (SIL OFL 1.1) — fonts/Pretendard-LICENSE.txt */')
# head
rep('<title>홀덤 GTO 퀴즈</title>\n<meta name="claude:viewport-fit-sides" content="cover">',
'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ALLIN IQ · 홀덤 GTO 퀴즈</title>
<meta name="description" content="ALLIN IQ — 홀덤 GTO 퀴즈와 프리플랍 오픈 연습">
<meta name="theme-color" content="#07090F">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ALLIN IQ">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">''')
rep('</style>\n','</style>\n</head>\n<body>\n',1) if False else None
i=s.index('</style>',s.index('<style>'));
# the game has several style blocks? close head after the last style that precedes <div class="app">
j=s.index('<div class="app">')
k=s.rindex('</style>',0,j)+len('</style>')
s=s[:k]+'\n</head>\n<body>'+s[k:]
# Firebase bridge: a classic script defines window.claude before the game script runs; the module fills it in
BRIDGE='''
<script>
window.HGQ_WEB=true;window.APP_VERSION="%s";
(function(){let res;const ready=new Promise(r=>res=r);window.__fbSet=a=>res(a);
  setTimeout(()=>res(null),15000);
  window.claude={use:async n=>{const a=await ready;if(!a)return null;return n==="db"?a.db:n==="user"?a.user:null}};})();
</script>
<script type="module" src="fb.js"></script>
'''%VER
rep('<script>\nconst POS=',BRIDGE+'<script>\nconst POS=')
rep('menu();\nlbInit();\n</script>','menu();\nlbInit();\n</script>\n<script src="webgate.js?v=%s"></script>'%VER)
s=s.rstrip()+'\n</body>\n</html>\n'
# ---- texts that described claude.ai sharing
rep('<p class="lbw">claude.ai에 로그인한 상태에서 이 링크를 열어야 참가할 수 있어요. 로그인한 뒤 링크를 다시 열어 주세요.</p>','<p class="lbw">서버에 연결하지 못했어요. 인터넷 연결을 확인하고 새로고침해 주세요.</p>')
rep('<b>로그인이 필요해요</b></div><p class="lbw">서버에','<b>연결할 수 없어요</b></div><p class="lbw">서버에')
rep('gs==="signin"?"claude.ai에 로그인한 상태에서 열어야 참가할 수 있어요."','gs==="signin"?"서버에 연결하지 못했어요. 새로고침해 주세요."')
rep('<p class="note" style="text-align:left">공유된 페이지에서 열면 함께 푸는 사람들의 순위가 여기에 보여요.</p>','<p class="note" style="text-align:left">서버에 연결되면 함께 푸는 사람들의 순위가 여기에 보여요.</p>')
i=s.index('<p class="lbs">이 페이지가 열려 있는 동안 접속한 초대 플레이어의 점수가 실시간으로 저장돼요.');j=s.index('</p>',i)+4
s=s[:i]+'<p class="lbs">플레이어 점수는 각자 실시간으로 저장돼요. 차단하면 그 사람은 게임과 순위에서 빠져요.</p>'+s[j:]
i=s.index("""    <p class="lbw">'링크가 있는 누구나'로 들어온 사람은""");j=s.index('</p>',i)+4
s=s[:i]+s[j:]
i=s.index("""     <li>'링크가 있는 누구나'로 공유하면""");j=s.index('</ul>',i)
s=s[:i]+'''     <li>링크를 받은 사람은 접속 코드·닉네임·비밀번호로 가입해야 게임을 할 수 있어요. 코드는 서버에서 확인해요.</li>
     <li>닉네임은 한 사람만 쓸 수 있고 바꿀 수 없어요. 다른 기기에서도 같은 닉네임과 비밀번호로 이어서 해요.</li>
     <li>비밀번호를 잊은 플레이어는 플레이어 관리에서 '비밀번호 초기화'를 눌러 받은 6자리 확인 코드를 알려 주면 돼요.</li>
     <li>코드를 바꾸면 이미 들어온 사람도 새 코드를 다시 입력해야 하고, 그 전까지는 점수가 저장되지 않아요.</li>
     <li>관리자는 등록된 구글 계정으로 로그인한 사람만 될 수 있어요. 순위·설정·차단은 서버 규칙으로 관리자만 바꿀 수 있어요.</li>
     <li>플레이어 화면에서는 우클릭·복사·드래그·저장·인쇄·소스보기 단축키를 막아 두었어요.</li>'''+s[j:]
# admin badge without a live room
rep('''<span class="badge2 ${LB.room?"on":""}">${LB.room?`접속 ${on}명`:"실시간 꺼짐"}</span>''','''<span class="badge2 on">${LB.room?`접속 ${on}명`:"실시간 저장"}</span>''')
# a stale member record (code changed) makes the save fail: send the player back to the code screen
rep('''  }while(LB.again)}catch(e){if(e&&e.code==="invalid_argument"){LB.writeFail=true;if(SCREEN==="menu")lbRender()}}''',
'''  }while(LB.again)}catch(e){if(e&&e.code==="invalid_argument"){LB.writeFail=true;if(window.HGQ_WEB&&!LB.owner){lsSet("hgq-acc","");ACC.sig=null;gateCheck()}if(SCREEN==="menu")lbRender()}}''')
# ---- admin sign-in link and update notice on the start screen
rep('''  $("go").onclick=()=>gateGo(()=>start(0));
  $("go2").onclick=()=>gateGo(()=>drillStart());''','''  $("go").onclick=()=>gateGo(()=>start(0));
  $("go2").onclick=()=>gateGo(()=>drillStart());
  if(window.HGQ_AUTH){const p=$("panel");const a=document.createElement("div");a.className="admrow";
    a.innerHTML=window.HGQ_AUTH.isAdmin?`<span>${esc(window.HGQ_AUTH.email)}</span><button class="lnk" id="admOut">관리자 로그아웃</button>`:window.HGQ_AUTH.anon?`<button class="lnk" id="admIn">관리자 로그인</button>`:"";if(a.innerHTML)p.appendChild(a);
    const i=$("admIn");if(i)i.onclick=()=>window.HGQ_AUTH.admin();const o=$("admOut");if(o)o.onclick=()=>window.HGQ_AUTH.out();}''')
rep('''  $("jBack").onclick=()=>{ACC.pending=null;menu()};''','''  $("jBack").onclick=()=>{ACC.pending=null;menu()};
  if(window.HGQ_AUTH&&!window.HGQ_AUTH.isAdmin){const a=document.createElement("div");a.className="admrow";a.innerHTML=`<button class="lnk" id="admIn2">관리자 로그인</button>`;$("panel").appendChild(a);$("admIn2").onclick=()=>window.HGQ_AUTH.admin()}''')
rep('${LB.room?`<span class="livetag"><i class="dot"></i>실시간</span> `:""}','${LB.room||window.HGQ_WEB?`<span class="livetag"><i class="dot"></i>실시간</span> `:""}')
TAIL='''
<div id="upd" class="upd" hidden><span>새 버전이 있어요</span><button id="updGo">새로고침</button></div>
<script>
// new-version notice: version.json is rewritten on every deploy
(function(){const chk=async()=>{try{const r=await fetch("version.json?t="+Date.now(),{cache:"no-store"});const j=await r.json();
  if(j.v&&j.v!==window.APP_VERSION)document.getElementById("upd").hidden=false}catch(e){}};
  document.getElementById("updGo").onclick=()=>location.reload();
  setInterval(chk,5*60*1000);document.addEventListener("visibilitychange",()=>{if(!document.hidden)chk()});setTimeout(chk,8000);
  if("serviceWorker" in navigator&&location.protocol==="https:")navigator.serviceWorker.register("sw.js").catch(()=>{});})();
</script>
'''
s=s.replace('\n</body>\n</html>\n',TAIL+'</body>\n</html>\n')
CSS='''
.admrow{display:flex;align-items:center;justify-content:center;gap:10px;font-size:12px;color:#6E6A62;margin-top:4px}
.admrow .lnk{font-size:12px;color:#8A8478;min-height:40px}
.upd{position:fixed;left:50%;bottom:calc(16px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:50;display:flex;align-items:center;gap:12px;padding:10px 12px 10px 18px;border-radius:999px;background:#14120E;border:1px solid #D4AF7C;box-shadow:0 10px 30px rgba(0,0,0,.6);color:#EAD3AE;font-size:14px;white-space:nowrap}
.upd[hidden]{display:none}.upd button{min-height:40px;border:0;border-radius:999px;padding:0 16px;background:linear-gradient(160deg,#F0D7AE,#C79E66);color:#0B0A08;font-weight:800;font-size:14px}
'''
k=s.rindex('</style>',0,s.index('</head>'))
s=s[:k]+CSS+s[k:]
open(OUT,'w',encoding='utf8').write(s)
json.dump({"v":VER},open(os.path.join(SITE,'version.json'),'w'))
print('built',OUT,len(s.encode()),'bytes, version',VER)
