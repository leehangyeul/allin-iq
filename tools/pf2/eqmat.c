// 169x169 프리플랍 핸드 클래스 승률표 (몬테카를로). 순서는 앱의 DH와 같음: 행 i·열 j, i==j 페어, i<j 수딧, i>j 오프수트. 랭크 0=A ... 12=2
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static uint64_t s[2]={0x9E3779B97F4A7C15ULL,0xD1B54A32D192ED03ULL};
static inline uint64_t rnd(void){uint64_t s1=s[0];const uint64_t s0=s[1];s[0]=s0;s1^=s1<<23;s[1]=s1^s0^(s1>>17)^(s0>>26);return s[1]+s0;}
static inline int rr(int n){return (int)(rnd()%n);}
// 카드: r(0..12, 0=2 ... 12=A)*4+suit
static int straight_hi(int m){ // m: 13비트 랭크 마스크(bit r), A는 12
  int x=m|((m>>12)&1)?0:0; (void)x;
  int mm=(m<<1)|((m>>12)&1); // bit0 = A low
  for(int h=13;h>=4;h--){ if(((mm>>(h-4))&31)==31) return h-1; }
  return -1;
}
static inline uint32_t enc(int cat,int a,int b,int c,int d,int e){return (cat<<20)|(a<<16)|(b<<12)|(c<<8)|(d<<4)|e;}
static uint32_t eval7(const int*cs){
  int cnt[13]={0},sm[4]={0},sc[4]={0},rm=0;
  for(int i=0;i<7;i++){int r=cs[i]>>2,su=cs[i]&3;cnt[r]++;sm[su]|=1<<r;sc[su]++;rm|=1<<r;}
  for(int su=0;su<4;su++) if(sc[su]>=5){int sf=straight_hi(sm[su]); if(sf>=0) return enc(8,sf,0,0,0,0);
     int k[5],n=0; for(int r=12;r>=0&&n<5;r--) if(sm[su]&(1<<r)) k[n++]=r; return enc(5,k[0],k[1],k[2],k[3],k[4]);}
  int q=-1,t[3],nt=0,p[3],np=0,sg[7],ns=0;
  for(int r=12;r>=0;r--){ if(cnt[r]==4)q=r; else if(cnt[r]==3)t[nt++]=r; else if(cnt[r]==2)p[np++]=r; else if(cnt[r]==1)sg[ns++]=r; }
  if(q>=0){int k=-1; for(int r=12;r>=0;r--) if(r!=q&&cnt[r]){k=r;break;} return enc(7,q,k,0,0,0);}
  if(nt>=1&&(np>=1||nt>=2)){int pp=np?p[0]:-1; if(nt>=2&&t[1]>pp)pp=t[1]; return enc(6,t[0],pp,0,0,0);}
  int st=straight_hi(rm); if(st>=0) return enc(4,st,0,0,0,0);
  if(nt==1){int k[2],n=0; for(int r=12;r>=0&&n<2;r--) if(r!=t[0]&&cnt[r]) k[n++]=r; return enc(3,t[0],k[0],k[1],0,0);}
  if(np>=2){int k=-1; for(int r=12;r>=0;r--) if(r!=p[0]&&r!=p[1]&&cnt[r]){k=r;break;} return enc(2,p[0],p[1],k,0,0);}
  if(np==1){int k[3],n=0; for(int r=12;r>=0&&n<3;r--) if(r!=p[0]&&cnt[r]) k[n++]=r; return enc(1,p[0],k[0],k[1],k[2],0);}
  return enc(0,sg[0],sg[1],sg[2],sg[3],sg[4]);
}
// 클래스 i(0..168) → 랭크 a,b(0=2..12=A), 종류
static void cls(int i,int*a,int*b,int*kind){int r=i/13,c=i%13; int ra=12-r,rb=12-c; if(r==c){*a=ra;*b=ra;*kind=0;} else if(r<c){*a=ra;*b=rb;*kind=1;} else {*a=rb;*b=ra;*kind=2;}}
static void deal_cls(int i,int*c1,int*c2,const int*used){
  int a,b,k; cls(i,&a,&b,&k);
  for(;;){ int s1=rr(4),s2=rr(4);
    if(k==0){ if(s1==s2) continue; } else if(k==1){ s2=s1; } else { if(s1==s2) continue; }
    int x=a*4+s1,y=b*4+s2; if(used[x]||used[y]) continue; *c1=x;*c2=y; return; }
}
int main(int argc,char**argv){
  int N=argc>1?atoi(argv[1]):20000; static double M[169][169];
  for(int i=0;i<169;i++) for(int j=i;j<169;j++){
    double w=0; int ok=0;
    for(int t=0;t<N;t++){
      int used[52]={0},h1,h2,v1,v2; deal_cls(i,&h1,&h2,used); used[h1]=used[h2]=1;
      // j 클래스가 히어로 카드와 겹쳐 불가능한 경우(예: AA vs AA는 가능, 카드 4장 필요) 대비 시도 횟수 제한
      int tries=0,okd=0; while(tries++<50){ int a,b,k; cls(j,&a,&b,&k); int s1=rr(4),s2=rr(4);
        if(k==0&&s1==s2) continue; if(k==1) s2=s1; if(k==2&&s1==s2) continue;
        int x=a*4+s1,y=b*4+s2; if(used[x]||used[y]) continue; v1=x;v2=y;okd=1;break; }
      if(!okd) continue; used[v1]=used[v2]=1; ok++;
      int bd[5],n=0; while(n<5){int c=rr(52); if(used[c]) continue; used[c]=1; bd[n++]=c;}
      int A[7]={h1,h2,bd[0],bd[1],bd[2],bd[3],bd[4]},B[7]={v1,v2,bd[0],bd[1],bd[2],bd[3],bd[4]};
      uint32_t ea=eval7(A),eb=eval7(B); w+= ea>eb?1.0:(ea==eb?0.5:0.0);
    }
    M[i][j]=ok?w/ok:0.5; M[j][i]=1.0-M[i][j];
  }
  printf("[");
  for(int i=0;i<169;i++){printf(i?",[":"[");for(int j=0;j<169;j++)printf(j?",%.4f":"%.4f",M[i][j]);printf("]");}
  printf("]\n");return 0;
}
