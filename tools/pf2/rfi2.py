# 깊은 스택(25·40·75BB) 첫 진입 오픈 + 오픈 대응(3벳·콜·폴드) 근사 계산 (자체 계산, 칩 EV)
# 2026-11-02. rfi_model.py(3벳 없음, 범위가 너무 넓게 나옴)를 대신해요.
# 가정
#  - 9인 BB 앤티(1BB). 오픈 2BB(25BB)·2.2BB(40BB)·2.3BB(75BB). SB는 BB에게 3BB 레이즈 또는 림프.
#  - 뒤 사람은 순서대로 폴드/콜/3벳. 처음 반응한 한 명과만 겨뤄요(첫 반응자 모델, 카드 제거 무시).
#  - 3벳: 25BB는 올인. 40·75BB는 3벳(IP 3.2배, 블라인드 4배) → 오프너는 폴드/콜/4벳 올인 → 3벳한 쪽은 콜/폴드.
#  - 플랍을 보는 경우 승률 × 실현율. 실현율 = 자리(IP 0.95, OOP 0.78) × 핸드 모양(페어·수딧 높고 연결 안 된 오프수트 낮음).
#  - BB가 아닌 자리의 콜은 뒤 사람(스퀴즈·추가 콜) 때문에 실현율 × 0.82.
#  - SB 림프: BB가 체크한다고 보고 OOP 실현율 × 0.85(BB 레이즈를 대신 반영).
#  - 반복 최적 대응(가상 플레이)으로 모든 전략을 함께 맞춰요.
import json,sys,numpy as np
from pushfold import DPOS,H,W,EQ,POST,ANTE,DEAD
RK="AKQJT98765432"
def shape():
    k=np.zeros(169)
    for n in range(169):
        i,j=divmod(n,13)
        if i==j:k[n]=1.0
        elif i<j:
            gap=j-i;k[n]=1.0+(0.04 if gap<=2 else 0)+(0.02 if i==0 else 0)
        else:
            a,b=j,i;gap=b-a
            if b<=4:k[n]=0.92
            elif a==0:k[n]=0.84
            elif gap<=2:k[n]=0.80
            else:k[n]=0.70
    return k
K=shape()
def R(ip):return (0.95 if ip else 0.78)*K
def eqv(rng):
    w=W*rng;s=w.sum()
    return (EQ@w)/s if s>1e-9 else np.full(169,0.5)
def frac(rng):return float((W*rng).sum()/W.sum())
def solve(S,iters=2000):
    r=2.0 if S<=30 else (2.2 if S<=50 else 2.3)
    out={"S":S,"open":{},"open_ev":{},"limp":{},"def":{}}
    for p in DPOS[:-1]:
        rr=3.0 if p=="SB" else r
        behind=DPOS[DPOS.index(p)+1:];bp=POST.get(p,0.0)
        O=np.where(np.arange(169)<40,1.0,0.0)
        T={q:np.where(np.arange(169)<8,1.0,0.0) for q in behind}   # 3벳
        C={q:np.where(np.arange(169)<25,1.0,0.0) for q in behind}  # 콜
        J={q:np.where(np.arange(169)<5,1.0,0.0) for q in behind}   # 오프너 4벳 올인(25BB는 3벳 올인에 콜)
        Kc={q:np.zeros(169) for q in behind}                         # 오프너 3벳 콜(40·75BB)
        A={q:np.where(np.arange(169)<5,1.0,0.0) for q in behind}   # 3벳한 쪽이 4벳 올인에 콜
        L=np.zeros(169)
        for it in range(1,iters+1):
            a=1.0/(it+1)
            evO=np.zeros(169);reach=1.0
            nT,nC,nJ,nK,nA={}, {}, {}, {}, {}
            eO=eqv(O)
            for q in behind:
                bq=POST.get(q,0.0);ipq=q not in("SB","BB");ipp=not ipq
                t=S if S<=30 else min(S,rr*(3.2 if ipq else 4.0))
                potC=DEAD-bp-bq+2*rr;potK=DEAD-bp-bq+2*t;pot2=DEAD-bp-bq+2*S
                # --- 반응자 q의 최적 대응 ---
                sq=1.0 if q=="BB" else 0.82   # 뒤에 남은 사람(스퀴즈·추가 콜) 때문에 콜러 실현율을 깎아요
                evC=sq*R(ipq)*eO*potC-(rr-bq)
                if S<=30:
                    # 3벳 올인: 오프너는 J(콜)로 받음
                    pj=float((W*O*J[q]).sum()/max((W*O).sum(),1e-9))
                    eJ=eqv(O*J[q])
                    ev3=(1-pj)*(DEAD-bp+rr)+pj*(eJ*pot2-(S-bq))
                else:
                    wO=(W*O).sum();pj=float((W*O*J[q]).sum()/max(wO,1e-9));pk=float((W*O*Kc[q]).sum()/max(wO,1e-9))
                    eJ=eqv(O*J[q]);eK=eqv(O*Kc[q])
                    callJ=np.maximum(eJ*pot2-(S-bq),-(t-bq))
                    nA[q]=((eJ*pot2-(S-bq))>-(t-bq)).astype(float)
                    ev3=(1-pj-pk)*(DEAD-bp+rr)+pj*callJ+pk*(R(ipq)*eK*potK-(t-bq))
                best=np.maximum(np.maximum(evC,ev3),0)
                nT[q]=((ev3>=evC)&(ev3>0)).astype(float);nC[q]=((evC>ev3)&(evC>0)).astype(float)
                # --- 오프너가 q를 만났을 때 ---
                f3=frac(T[q]);fc=frac(C[q])
                eC=eqv(C[q]);eT=eqv(T[q])
                vsC=R(ipp)*eC*potC-(rr-bp)
                if S<=30:
                    callv=eT*pot2-(S-bp);nJ[q]=(callv>-(rr-bp)).astype(float)
                    vs3=np.maximum(callv,-(rr-bp))
                else:
                    pa=float((W*T[q]*A[q]).sum()/max((W*T[q]).sum(),1e-9));eTA=eqv(T[q]*A[q])
                    jamv=(1-pa)*(DEAD-bq+t)+pa*(eTA*pot2-(S-bp))
                    callv=R(ipp)*eT*potK-(t-bp)
                    foldv=-(rr-bp)
                    nJ[q]=((jamv>=callv)&(jamv>foldv)).astype(float);nK[q]=((callv>jamv)&(callv>foldv)).astype(float)
                    vs3=np.maximum(np.maximum(jamv,callv),foldv)
                evO+=reach*(fc*vsC+f3*vs3);reach*=(1-fc-f3)
            evO+=reach*DEAD
            if p=="SB":
                # 림프: BB 체크, 팟 = 앤티+1+1
                evL=0.85*R(False)*eqv(np.ones(169))*(ANTE+2.0)-0.5
                nO=((evO>=evL)&(evO>0)).astype(float);nL=((evL>evO)&(evL>0)).astype(float)
                L=(1-a)*L+a*nL
            else:nO=(evO>0).astype(float)
            O=(1-a)*O+a*nO
            for q in behind:
                T[q]=(1-a)*T[q]+a*nT[q];C[q]=(1-a)*C[q]+a*nC[q];J[q]=(1-a)*J[q]+a*nJ[q]
                if S>30:Kc[q]=(1-a)*Kc[q]+a*nK[q];A[q]=(1-a)*A[q]+a*nA[q]
        rd=lambda v:[round(float(x),3) for x in v]
        out["open"][p]=rd(O);out["open_ev"][p]=rd(evO)
        if p=="SB":out["limp"][p]=rd(L)
        for q in behind:out["def"][q+"<"+p]={"3bet":rd(T[q]),"call":rd(C[q])}
    return out
def pct(v):return sum(W[i]*v[i] for i in range(169))/W.sum()*100
if __name__=="__main__":
    S=float(sys.argv[1]);it=int(sys.argv[2]) if len(sys.argv)>2 else 2000
    r=solve(S,it);json.dump(r,open(f"rfi2_{int(S)}.json","w"))
    print(int(S),"오픈",' '.join("%s %.0f%%"%(p,pct(r["open"][p])) for p in DPOS[:-1]),"| SB 림프 %.0f%%"%pct(r["limp"]["SB"]))
    for k in("BB<BTN","BB<UTG","BTN<CO","SB<BTN"):
        d=r["def"][k];print("  ",k,"3벳 %.0f%% 콜 %.0f%%"%(pct(d["3bet"]),pct(d["call"])))
