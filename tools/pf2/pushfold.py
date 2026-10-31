# 9인 BB 앤티 올인/폴드 계산 (첫 콜러 모델, 칩 EV). 반복 최적 대응(가상 플레이)으로 올인 범위와 콜 범위를 함께 맞춰요.
# 결과: jam[pos][169], jam_ev[pos][169], call["p>q"][169], call_ev["p>q"][169]  (EV는 폴드 대비 BB 단위)
import json,sys,numpy as np
DPOS=["UTG","UTG+1","UTG+2","LJ","HJ","CO","BTN","SB","BB"]
DRK="AKQJT98765432"
H=[(DRK[i]+DRK[i]) if i==j else (DRK[i]+DRK[j]+"s" if i<j else DRK[j]+DRK[i]+"o") for i in range(13) for j in range(13)]
W=np.array([6.0 if len(h)==2 else (4.0 if h[2]=="s" else 12.0) for h in H])
import os
EQ=np.array(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"eqmat.json"))))
POST={"SB":0.5,"BB":1.0};ANTE=1.0;DEAD=0.5+1.0+ANTE
def avail(pos,S):return S-ANTE if pos=="BB" else S
def solve(S,iters=1500):
    out={"jam":{},"jam_ev":{},"call":{},"call_ev":{}}
    for p in DPOS[:-1]:
        behind=DPOS[DPOS.index(p)+1:]
        P=np.where(np.arange(169)<30,1.0,0.0)   # 초기값
        C={q:np.where(np.arange(169)<20,1.0,0.0) for q in behind}
        Pavg=P.copy();Cavg={q:C[q].copy() for q in behind}
        bp=POST.get(p,0.0)
        for it in range(1,iters+1):
            # 콜하는 쪽: 올인 범위(평균)를 상대로 콜 EV
            wp=W*Pavg
            eqv=(EQ@wp)/max(wp.sum(),1e-9)          # 각 핸드 x가 올인 범위를 상대로 이길 확률
            newC={}
            for q in behind:
                m=min(avail(p,S),avail(q,S));bq=POST.get(q,0.0)
                pot=2*m+(DEAD-bp-bq)
                ev=eqv*pot-m+bq
                newC[q]=(ev>0).astype(float)
            # 올인하는 쪽: 첫 콜러 확률과 콜 범위 상대 승률
            ev_j=np.zeros(169);reach=1.0
            for q in behind:
                cq=Cavg[q];f=(W*cq).sum()/W.sum()       # 이 자리가 콜하는 비율(카드 제거 무시)
                m=min(avail(p,S),avail(q,S));bq=POST.get(q,0.0);pot=2*m+(DEAD-bp-bq)
                wc=W*cq;eqc=(EQ@wc)/max(wc.sum(),1e-9)
                ev_j+=reach*f*(eqc*pot-m+bp)
                reach*=(1-f)
            ev_j+=reach*DEAD
            newP=(ev_j>0).astype(float)
            a=1.0/(it+1)
            Pavg=(1-a)*Pavg+a*newP
            for q in behind:Cavg[q]=(1-a)*Cavg[q]+a*newC[q]
        # 마지막 EV(평균 전략 기준)
        wp=W*Pavg;eqv=(EQ@wp)/max(wp.sum(),1e-9)
        for q in behind:
            m=min(avail(p,S),avail(q,S));bq=POST.get(q,0.0);pot=2*m+(DEAD-bp-bq)
            out["call"][p+">"+q]=[round(float(x),3) for x in Cavg[q]];out["call_ev"][p+">"+q]=[round(float(x),3) for x in (eqv*pot-m+bq)]
        out["jam"][p]=[round(float(x),3) for x in Pavg];out["jam_ev"][p]=[round(float(x),3) for x in ev_j]
    return out
if __name__=="__main__":
    S=float(sys.argv[1]);r=solve(S,int(sys.argv[2]) if len(sys.argv)>2 else 1500)
    json.dump(r,open(f"pf_{int(S)}.json","w"))
    for p in DPOS[:-1]:
        pct=sum(W[i]*r["jam"][p][i] for i in range(169))/W.sum()*100;print(S,p,"올인 %.1f%%"%pct)
