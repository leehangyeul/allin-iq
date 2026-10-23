# 전체 점검: 빌드 결과·데이터·점수 계산·가입/순위·타이머·코치·전수 풀이를 한 번에 돌리고 요약해요
# 사용: python3 tools/webtest/audit.py   (저장소 루트에서)
import subprocess,sys,os,re,json,time
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(os.path.dirname(HERE))
TESTS=[("데이터(카드 중복·빈도 합)","t_chk.py"),("종합 점수·평균 계산","t_avg.py"),("측정 중 플레이어 숨김","t_wait.py"),
 ("가입·이어하기·차단·초기화","t_web2.py"),("종합 5판 규칙","t_all.py"),("20초 타이머","t_timer.py"),("코치 보드","t_coach.py"),("코치 기록 기기 간 합치기","t_coachsync.py"),
 ("전수 풀이(150핸드×4경로+연습400)","t_playall.py")]
BADWORDS=re.compile(r'Traceback|AssertionError|FAIL|NaN|undefined|✗|❌|오류:|이상 있음')
res=[]
# 정적 점검: 버전 파일, 빌드 결과, 금지 표현
st=[]
v=json.load(open(os.path.join(ROOT,'version.json')))['v'];html=open(os.path.join(ROOT,'index.html'),encoding='utf8').read()
st.append(("version.json 형식",bool(re.fullmatch(r'\d{12}',v)),v))
st.append(("index.html에 버전 반영",v in html,""))
for w in ["상금","현금","경품","환전"]:
    st.append((f"금지 표현 '{w}' 없음",w not in html,""))
for t in ["Jonathan","PokerCoaching","강의 PDF"]:
    n=html.count(t);st.append((f"출처 표기 '{t}' 화면 노출 {n}건",True,"(소스 주석은 허용, 화면 문구는 직접 확인)"))
for name,ok,info in st:print(("PASS" if ok else "FAIL"),name,info)
fails=[n for n,ok,_ in st if not ok]
for name,f in TESTS:
    t0=time.time()
    try:
        p=subprocess.run([sys.executable,os.path.join(HERE,f)],capture_output=True,text=True,timeout=900,cwd=ROOT)
        out=(p.stdout+p.stderr);bad=[l for l in out.splitlines() if BADWORDS.search(l) and 'ERR_FAILED' not in l and '이상 없음' not in l and 'no data errors' not in l]
        ok=p.returncode==0 and not bad
    except Exception as e:
        ok=False;bad=[str(e)];out=''
    print(("PASS" if ok else "FAIL"),name,f"({time.time()-t0:.0f}s)")
    for l in bad[:5]:print("   ",l[:160])
    if not ok:fails.append(name)
print("\n결과:", "모두 통과" if not fails else "실패 "+", ".join(fails));sys.exit(1 if fails else 0)
