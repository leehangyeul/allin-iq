# 프리플랍 첫 결정 해설 문장을 합친 차트와 정답(가장 높은 빈도)에 맞춰 새로 써요. 2026-11-02
# 입력: cmp1102.json (chartAlign 전 old / 후 new 비교), 출력: notes1102.json {"자리|핸드|0": 해설}
import json,sys
d=json.load(open(sys.argv[1]));O,N=d["old"],d["new"]
RV="23456789TJQKA"
def jong(w):
    c=w.rstrip()[-1]
    if "가"<=c<="힣":return (ord(c)-0xAC00)%28!=0
    return c in "0136789LMNRlmnr"
def eul(w):return w+("을" if jong(w) else "를")
def iga(w):return w+("이" if jong(w) else "가")
def cls(hand):
    r1,s1,r2,s2=hand[0],hand[1],hand[2],hand[3]
    a,b=sorted([r1,r2],key=lambda x:-RV.index(x))
    return a+b if a==b else a+b+("s" if s1==s2 else "o")
def feature(c):
    a,b=c[0],c[1];ia,ib=RV.index(a),RV.index(b);s=len(c)==3 and c[2]=="s"
    if a==b:return "하이 페어라 상대 레인지 대부분에 앞서요" if ia>=RV.index("T") else "스몰·미들 페어라 셋 마이닝 가치가 있어요"
    if a=="A":return ("A 블로커가 있고 넛 플러시 드로우를 만들 수 있어요" if s else ("A 블로커에 키커도 좋아 하이카드 가치가 커요" if ib>=RV.index("T") else "A 블로커는 있지만 키커가 약해 도미네이트되기 쉬워요"))
    gap=ia-ib
    if s and gap<=2:return "수딧 커넥터라 플레이어빌리티가 좋아요"
    if s:return "수딧이라 플러시 에퀴티는 있지만 커넥트가 약해요"
    if ib>=RV.index("T"):return "브로드웨이 오프수트라 하이카드 가치는 있지만 플레이어빌리티가 낮아요"
    return "오프수트에 갭도 커서 플레이어빌리티가 낮아요"
def word(lbl):return lbl.split(" ")[0]
def eun(w):return w+("은" if jong(w) else "는")
def ro(w):
    c=w.rstrip()[-1]
    if "가"<=c<="힣":k=(ord(c)-0xAC00)%28;return w+("로" if k in (0,8) else "으로")
    return w+("으로" if c in "0368" else "로")
def wa(w):return w+("과" if jong(w) else "와")
TAIL={"오픈":"레이즈로 이니셔티브를 가져가요","레이즈":"레이즈로 이니셔티브를 가져가요","림프":"림프로 팟을 작게 유지해요",
      "폴드":"이 포지션에선 폴드가 EV 손실이 적어요","콜":"프라이스가 좋아 콜로 플랍을 봐요","3벳":"3벳으로 이니셔티브를 잡고 폴드 에퀴티도 챙겨요",
      "4벳":"4벳으로 팟을 키워요","5벳":"5벳으로 맞서요","올인":"잼으로 폴드 에퀴티와 에퀴티를 함께 챙겨요"}
out={};rows=[]
for o,n in zip(O,N):
    mixed=bool(n["cell"] and len(n["cell"].split(" ")[1])>1)
    need=bool(n["cell"]) or o["top"]!=n["top"] or (mixed and "섞" not in n["n"]) or "차트" in n["n"]   # 차트가 붙는 첫 결정은 모두 쉬운 말 템플릿으로
    if not need:continue
    lab={k:word(l) for k,l in n["o"]}
    f={kv.split(":")[0]:float(kv.split(":")[1]) for kv in n["f"].split(" ")}
    order=sorted(f,key=lambda k:-f[k]);top,sec=order[0],order[1] if len(order)>1 else None
    a=n["a"];c=cls(n["hand"]);ft=feature(c);D=n["d"]
    if n["cell"]:
        key=n["cell"].split(" ")[0];S={"O":None}
        S=[x for x in (15,25,40,75) if (D<20 and x==15) or (20<=D<=32 and x==25) or (32<D<=57 and x==40) or (D>57 and x==75)][0]
        SL="100-75BB" if S==75 else f"{S}BB"
        stk="" if (D==S or (S==75 and 75<=D<=100)) else f" {D}BB 차트가 없어 가장 가까운 차트를 써요."
        if key.startswith("O:"):situ=f"{D}BB {n['me']} RFI(앞에서 모두 폴드)."
        else:situ=f"{D}BB {n['me']} vs {n['vs']} {'레이즈' if n['vs']=='SB' else '오픈'}."
        T,Sx=lab[top],(lab[sec] if sec else None)
        isd=key.startswith("D:");sbo=key=="O:SB"
        nm={"r":"3벳" if isd else ("레이즈" if n["me"]=="SB" else "오픈"),"j":"올인","c":"콜","l":"림프","f":"폴드"}
        def let(k):return "f" if k=="fold" else "j" if k=="jam" else ("l" if sbo else "c") if k=="call" else "r"
        have={let(k):lab[k] for k,_ in n["o"]}
        for L_,w_ in have.items():nm[L_]=w_
        if mixed:
            cl=n["cell"].split(" ")[1];sv,ot=nm[cl[0]],nm[cl[1]]
            head=f"{situ}{stk} {SL} 통합 차트에서 {eun(c)} {sv}·{ot} 믹스 핸드예요. {ft}."
            tl=let(top);ml=[x for x in cl if x!=tl]
            if ml and ml[0] not in have:
                t=f"{head} 이 문제엔 {nm[ml[0]]} 선택지가 없어서 {iga(T)} 정답이에요."
            else:
                t=f"{head} {T} {int(f[top])}% · {Sx} {int(f[sec])}%로 섞어요."
        else:
            t=f"{situ}{stk} {SL} 통합 차트에서 {eun(c)} {T} 칸이에요. {ft}. {TAIL.get(T,'')}."
            if sec and f[sec]>=20:t+=f" {Sx}도 {int(f[sec])}% 섞어요."
        if n.get("mult"):t+=" 앞에 콜러가 있어 1:1 오픈 대응 차트로 근사했고, 데드머니만큼 더 넓게 참여할 수 있어요."
    else:
        T=lab[top];Sx=lab[sec] if sec else None
        if "빌런 4벳" in a:pre="4벳을 맞은 뒤"
        elif "빌런 3벳" in a:pre="3벳을 맞은 뒤"
        else:pre="이 상황에서"
        T2={"레이즈":"5벳" if "4벳" in pre else "4벳","오픈":"4벳"}.get(T,T);S2={"레이즈":"5벳" if "4벳" in pre else "4벳","오픈":"4벳"}.get(Sx,Sx) if Sx else None
        body="3벳 레인지 상대로 에퀴티와 플레이어빌리티가 부족해요" if T=="폴드" and "3벳" in pre else ("4벳 레인지 상대로 에퀴티가 부족해요" if T=="폴드" else ft)
        t=f"{pre} {c} 핸드는 {iga(T2)} 기본이에요. {body}."+(f" {S2}도 {int(f[sec])}% 섞어요." if sec and f[sec]>=15 else "")
        if sec and abs(f[top]-f[sec])<=2:t=f"{pre} {c} 핸드는 {wa(T2)} {S2}를 반반 섞어요. {ft}."
    k=f"{n['me']}|{n['hand']}|0"
    if k in out:print("중복 키",k)
    out[k]=t;rows.append((n["id"],k,n["f"],t))
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False,indent=0)
for r in rows:print(r[0],r[1],"|",r[2],"\n   ",r[3])
print(len(out),"개")
