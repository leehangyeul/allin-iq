# 사용자 솔버(GTO 홀덤 테이블)의 프리플랍 차트(solver_charts.json)와 기존 기준 차트(RANGES)를 합쳐 하나의 차트를 만들어요. 2026-11-02
# solver_charts.json은 GTO 홀덤 테이블(gto/orig.html)의 buildCharts(15·25·40·75)를 그대로 뽑은 값이에요.
# (예전 자체 계산 rfi2_*.json으로 합치려면 SRC 뒤에 rfi2 를 붙여요)
# 규칙: 둘 다 같은 행동 → 그 행동(공통 분모) / 서로 다르면 → 믹스(두 액션). 결과는 출처 구분 없는 '통합 GTO 차트'. 75BB 칸은 100-75BB 공통 차트로 써요.
# 행동: 오픈·작은 3벳 r · 림프 l · 올인 j · 콜 c · 폴드 f. 계산의 3벳은 25BB 이하면 올인(j), 40·75BB면 작은 3벳(r).
# 출력: merged.json = {S: {key: {"g": 주 행동 169글자, "x": 섞을 때 둘째 행동 또는 "."}}}
import json,re,sys,numpy as np
from pushfold import W
SRC=sys.argv[1]
s=open(SRC,encoding="utf-8").read()
RANGES=json.loads(re.search(r'const RANGES=(\{.*?\});',s).group(1))
PF15=json.load(open("pf_15.json"))
M={S:json.load(open(f"rfi2_{S}.json")) for S in (15,25,40,75)}
MIX=0.25  # 계산에서 이 비율 이상 나온 행동은 '쓰는 행동'으로 봐요
def avg(vs):return list(np.mean(np.array(vs),axis=0))
def fam(c,S):
    return c
def ours_open(S,p):
    m=M[S];o=np.array(m["open"][p]);ev=np.array(m["open_ev"][p])
    res=[]
    for i in range(169):
        acts={}
        if p=="SB":
            l=m["limp"]["SB"][i];acts["r"]=o[i];acts["l"]=l;acts["f"]=max(0,1-o[i]-l)
        else:acts["r"]=o[i];acts["f"]=1-o[i]
        if S==15 and p!="SB":
            # 15BB: 작은 오픈과 올인 중 EV가 높은 쪽
            jev=PF15["jam_ev"][p][i]
            if jev>max(ev[i],0)+0.05:acts={"j":PF15["jam"][p][i],"f":1-PF15["jam"][p][i]}
        res.append(acts)
    return res
def ours_def(S,dg,og):
    m=M[S]["def"]
    ds={"UTG+1/+2":["UTG+1","UTG+2"],"LJ/HJ":["LJ","HJ"]}.get(dg,[dg])
    os_={"LJ/HJ":["LJ","HJ"]}.get(og,[og])
    pairs=[(d,o) for d in ds for o in os_ if d+"<"+o in m]
    t=avg([m[d+"<"+o]["3bet"] for d,o in pairs]);c=avg([m[d+"<"+o]["call"] for d,o in pairs])
    a3="j" if S<=25 else "r"
    return [{a3:t[i],"c":c[i],"f":max(0,1-t[i]-c[i])} for i in range(169)]
SV=json.load(open("solver_charts.json"))
USE_SOLVER=not (len(sys.argv)>2 and sys.argv[2]=="rfi2")
SPOS={"UTG+1":"UTG1","UTG+2":"UTG2"}
def sv_open(S,p):
    C=SV[str(S)];res=[]
    for i in range(169):
        if p=="SB":acts={"r":C["sb.raise"][i],"j":C["sb.jam"][i],"l":C["sb.limp"][i]}
        else:q=SPOS.get(p,p);acts={"r":C[f"rfi.{q}.raise"][i],"j":C[f"rfi.{q}.jam"][i]}
        acts={k:v for k,v in acts.items() if v>0};acts["f"]=max(0.0,1-sum(acts.values()));res.append(acts)
    return res
def sv_def(S,dg,og):
    C=SV[str(S)]
    if og=="SB":bases=["bbr"]
    else:
        grp={"UTG":"EP","LJ/HJ":"MP","LJ":"MP","CO":"CO","BTN":"BTN"}[og]
        ds={"UTG+1/+2":["UTG1","UTG2"],"LJ/HJ":["LJ","HJ"]}.get(dg,[dg])
        bases=[f"def.{grp}.{d}" for d in ds if f"def.{grp}.{d}.call" in C]
    res=[]
    for i in range(169):
        t=np.mean([C[b+".threebet"][i] for b in bases]);j=np.mean([C[b+".jam"][i] for b in bases]);c=np.mean([C[b+".call"][i] for b in bases])
        acts={k:v for k,v in {"r":t,"j":j,"c":c}.items() if v>0};acts["f"]=max(0.0,1-t-j-c);res.append(acts)
    return res
def norm(L,S,key):
    # 기준 차트 글자를 같은 묶음으로: 3벳은 스택에 맞춰 j/r 하나로
    return L   # 작은 3벳(r)과 올인 3벳(j)은 다른 행동으로 봐요(갈리면 섞음)
out={};stat={}
for S in ("15","25","40","75"):
    out[S]={};Si=int(S)
    for key,v in RANGES[S].items():
        if key.startswith("O:"):ours=(sv_open if USE_SOLVER else ours_open)(Si,key[2:])
        else:
            dg,og=key[2:].split("<");ours=(sv_def if USE_SOLVER else ours_def)(Si,dg,og)
        g=[];x=[];n_mix=0
        for i in range(169):
            L=norm(v["g"][i],Si,key);acts=ours[i]
            if key.startswith("O:") and L=="j" and "j" not in acts:L="r"   # 첫 진입 올인은 '오픈' 묶음으로
            top=max(acts,key=acts.get);used=sorted([a for a,f in acts.items() if f>=MIX],key=lambda a:-acts[a])
            if used==[L] or (len(used)==1 and used[0]==L):g.append(L);x.append(".")
            elif L in used:
                other=[a for a in used if a!=L][0];g.append(top);x.append(L if top!=L else other);n_mix+=1
            else:g.append(top);x.append(L);n_mix+=1
        if Si==25 and key.startswith("D:"):
            dg,og=key[2:].split("<")
            if dg not in ("SB","BB") and og in ("UTG","LJ/HJ"):
                # 기준 규칙: 20~34BB에서 IP가 앞·중간 포지션 오픈을 받으면 3벳은 올인이 아니라 작은 3벳
                g=["r" if a=="j" else a for a in g];x=["r" if a=="j" else a for a in x]
                x=["." if a==b else b for a,b in zip(g,x)]
        # 통합 차트: 출처 구분 없이 믹스 칸은 액션 순서(오픈·3벳 → 올인 → 림프 → 콜 → 폴드)로 왼쪽·오른쪽을 정해요
        RNK="rjlcf"
        for i in range(169):
            if x[i]!="." and RNK.index(x[i])<RNK.index(g[i]):g[i],x[i]=x[i],g[i]
        out[S][key]={"g":"".join(g),"x":"".join(x)}
        stat[S+" "+key]=n_mix
json.dump(out,open("merged.json","w"),ensure_ascii=False)
for k,v in stat.items():print(k,"섞음",v)
