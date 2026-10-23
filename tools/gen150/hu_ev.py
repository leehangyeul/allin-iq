# 헤즈업 푸시/폴드 균형(hu_nash.json) 기준으로 핸드별 EV(BB, 칩EV, ICM 없음)를 계산해요
import json, numpy as np
d=json.load(open('eqmat.json'));n=169
eq=np.array([[d[i][j][0] for j in range(n)] for i in range(n)]);w=np.array([[d[i][j][1] for j in range(n)] for i in range(n)],float)
R="AKQJT98765432";names=[]
for r in range(13):
    for c in range(13):
        if r==c: names.append(R[r]*2)
        elif c>r: names.append(R[r]+R[c]+"s")
        else: names.append(R[c]+R[r]+"o")
H=json.load(open('own/hu_nash.json'));out={}
for S in (10,15,20,25):
    push=np.array([H[str(S)]["push"][x] for x in names]);call=np.array([H[str(S)]["call"][x] for x in names])
    pcw=w*call[None,:]
    pc=pcw.sum(1)/w.sum(1)
    evj=(1-pc)+(pcw*(2*eq-1)).sum(1)*S/w.sum(1)      # SB 올인 EV
    ww=w.T*push[None,:];tot=ww.sum(1)+1e-12
    evc=(ww*(2*(1-eq.T)-1)).sum(1)*S/tot              # BB 콜 EV
    out[str(S)]={"sb":{x:round(float(v+0.5),3) for x,v in zip(names,evj)},"bb":{x:round(float(v+1.0),3) for x,v in zip(names,evc)}}
    chk=[(names[i],round(float(evj[i]+.5),2)) for i in (0,12,168,100)]
    print(S,chk,"SB올인 평균이득",round(float((evj+.5)[push>.5].mean()),2))
json.dump(out,open('own/hu_ev.json','w'))
