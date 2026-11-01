# 참고용(사용 안 함): 깊은 스택 오픈 근사 모델. 3벳을 고려하지 않아 범위가 비현실적으로 넓게 나와 앱에 쓰지 않기로 함(2026-11-01).
# 깊은 스택(25·40·75BB) 첫 진입 오픈/폴드 근사 모델 (자체 계산 근사)
# 가정: 오픈 크기 2BB(25BB)·2.2BB(40·75BB)·SB 3.5BB, 뒤 사람은 콜 아니면 폴드(3벳·스퀴즈는 넣지 않음), 처음 콜한 한 명과만 플랍,
#       에퀴티 실현율: 포지션 있는 쪽 0.95, 없는 쪽 0.80 (블라인드 방어자는 0.75). 반복 최적 대응으로 오픈 범위와 콜 범위를 함께 맞춰요.
import json,sys,numpy as np
from pushfold import DPOS,H,W,EQ,POST,ANTE,DEAD
def solve(S,iters=1500):
    out={"open":{},"open_ev":{}}
    for p in DPOS[:-1]:
        r=3.5 if p=="SB" else (2.0 if S<=30 else 2.2)
        behind=DPOS[DPOS.index(p)+1:];bp=POST.get(p,0.0)
        O=np.where(np.arange(169)<40,1.0,0.0);C={q:np.where(np.arange(169)<30,1.0,0.0) for q in behind}
        for it in range(1,iters+1):
            wo=W*O;eqv=(EQ@wo)/max(wo.sum(),1e-9);newC={}
            for q in behind:
                bq=POST.get(q,0.0);pot=2*r+(DEAD-bp-bq)
                Rq=0.75 if q in("SB","BB") else 0.95
                newC[q]=((Rq*eqv*pot-(r-bq))>0).astype(float)
            ev=np.zeros(169);reach=1.0
            for q in behind:
                cq=C[q];f=(W*cq).sum()/W.sum();bq=POST.get(q,0.0);pot=2*r+(DEAD-bp-bq)
                Rp=0.95 if q in("SB","BB") and p!="SB" else 0.80
                wc=W*cq;eqc=(EQ@wc)/max(wc.sum(),1e-9)
                ev+=reach*f*(Rp*eqc*pot-r+bp);reach*=(1-f)
            ev+=reach*DEAD
            a=1.0/(it+1);O=(1-a)*O+a*(ev>0)
            for q in behind:C[q]=(1-a)*C[q]+a*newC[q]
        out["open"][p]=[round(float(x),3) for x in O];out["open_ev"][p]=[round(float(x),3) for x in ev]
    return out
if __name__=="__main__":
    S=float(sys.argv[1]);r=solve(S);json.dump(r,open(f"rfi_{int(S)}.json","w"))
    print(S,' '.join("%s %.1f%%"%(p,sum(W[i]*r["open"][p][i] for i in range(169))/W.sum()*100) for p in DPOS[:-1]))
