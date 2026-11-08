import sys,struct as S,zlib
sys.path.insert(0,'/tmp/claude-0')
from hwplib import recs,enc,comp
import olefile
f=olefile.OleFileIO('/tmp/claude-0/v2/in.hwp')
R=[list(x) for x in recs(zlib.decompress(f.openstream('BodyText/Section1').read(),-15))]
P_HDR,P_TXT,P_CS,P_LS=66,67,68,69
def txtlen(b): return len(b)//2
def setpara(i,text,runs,prefix=b''):
    """rewrite paragraph whose header is R[i]; returns nothing, mutates R (lineseg removed later)"""
    l=R[i][1]; h=bytearray(R[i][2]); assert R[i][0]==P_HDR
    body=prefix+text.encode('utf-16le')+b'\r\0'; n=len(body)//2
    last=S.unpack('<I',h[:4])[0]&0x80000000
    h[0:4]=S.pack('<I',n|last); h[12:14]=S.pack('<H',len(runs)); h[14:16]=S.pack('<H',0); h[16:18]=S.pack('<H',0)
    R[i][2]=bytes(h)
    j=i+1
    while j<len(R) and R[j][1]>l:
        if R[j][1]==l+1 and R[j][0]==P_TXT: R[j][2]=body
        elif R[j][1]==l+1 and R[j][0]==P_CS: R[j][2]=b''.join(S.pack('<II',a,c) for a,c in runs)
        elif R[j][1]==l+1 and R[j][0] in (P_LS,70): R[j][0]=None
        j+=1
def txt_of(i): return R[i+1][2]
B=0x3  # body cs (한양신명조 9)
# ---- abstract (143): keep pgnp ctrl prefix
pre=R[144][2][:16]
old=R[144][2][16:].decode('utf-16le')
k=old.index('원본 영상 20개')
abs_new=old[:k]+'영상 50개에 대한 실험에서 원본 성능은 시점 0.375, 위치 0.655로 단순 기준선보다 크게 높아 평가 절차가 정상적으로 동작함을 확인하였다. 열화를 적용하면 위치 판단은 9개 조건 중 8개에서 2~8% 낮아졌고, 시점 판단은 약한 열화에서는 거의 변하지 않았으나 가장 강한 해상도 저하와 모션 블러에서 각각 20.6%, 13.4% 낮아지는 경향을 보였다.'
setpara(143,abs_new,[(0,B),(8,0xf)],prefix=pre)
# ---- 4.1 (486)
setpara(486,'  열화를 적용하기 전에 원본 영상에서 성능을 확인하였다(표 3). 무작위로 추출한 영상 50개에서 Molmo-7B-D는 시점 0.375, 위치 0.655로 단순 기준선(영상 중앙 시각, 화면 중앙 좌표)보다 크게 높아 평가 절차가 정상적으로 동작함을 확인하였다. 영상별 점수가 0 또는 1에 가깝게 나뉘는 경향이 있어 표본이 작을 때 평균이 보고값과 차이를 보일 수 있다. 시점 판단에서 사고를 한 번도 탐지하지 못한 영상은 16%였다.',[(0,B)])
# ---- table 3 last row
for i,t in ((574,'50'),(579,'0.375'),(584,'0.655')): setpara(i,t,[(0,0x28)])
# ---- 4.2 (592)
setpara(592,'  표 4는 영상 50개에 대해 원본과 열화 9개 조건의 시점·위치 점수와 원본 대비 하락률을 정리한 것이다. 하락률이 음수이면 원본보다 점수가 높아진 경우이다. 위치 판단은 9개 조건 중 8개에서 원본보다 점수가 낮아졌으나(하락률 2.3~8.1%), 95% 신뢰구간이 0을 포함하지 않은 것은 해상도 1/4 조건(8.1%)뿐이었다. 시점 판단은 약한·중간 단계의 열화에서는 원본과 뚜렷한 차이가 없었으나, 가장 강한 해상도 저하(1/8)와 모션 블러(17 px)에서 각각 20.6%, 13.4% 낮아졌고 사고를 탐지하지 못한 영상의 비율도 16%에서 24%로 늘었다. 다만 이 두 조건의 신뢰구간은 0을 포함하므로 하락 경향으로 해석하는 것이 적절하다. H.264 압축은 CRF 47까지 시점 판단에 거의 영향을 주지 않았고 위치 점수만 4~7% 낮아졌다. 또한 열화 단계가 강해질수록 성능이 꾸준히 낮아지는 모습은 나타나지 않았는데, 영상 수가 제한되어 영상별 점수의 변동이 평균에 크게 반영되었기 때문으로 보인다.',[(0,B)])
# ---- conclusion (749)
old=R[750][2].decode('utf-16le')[:-1]
a=old.index('(열화 결과'); b=old.index('1~2문장)')+len('1~2문장)')
con=old[:a]+'열화를 적용하면 위치 판단은 대부분의 조건에서 소폭(2~8%) 저하되고 시점 판단은 가장 강한 해상도 저하와 모션 블러에서 저하되는 경향을 보였다'+old[b:]
setpara(749,con,[(0,B)])
# ---- table 4 rebuild (ctrl at 607, cells from 609 .. 741)
M='−'
rows=[('원본','0.375','–','0.655','–'),
('해상도 1/2','0.352','6.1 [−1.9, 15.3]','0.666','−1.6 [−7.4, 2.7]'),
('해상도 1/4','0.384','−2.5 [−27.5, 16.8]','0.602','8.1 [1.9, 16.0]'),
('해상도 1/8','0.298','20.6 [−12.6, 45.5]','0.632','3.4 [−13.3, 17.6]'),
('H.264 CRF 37','0.389','−3.8 [−26.3, 13.4]','0.627','4.3 [−5.7, 13.5]'),
('H.264 CRF 42','0.369','1.5 [−29.3, 23.5]','0.607','7.2 [−4.4, 18.5]'),
('H.264 CRF 47','0.380','−1.4 [−43.6, 29.4]','0.615','6.1 [−7.8, 19.3]'),
('모션 블러 6 px','0.375','0.1 [−18.7, 15.1]','0.617','5.8 [−2.7, 14.5]'),
('모션 블러 11 px','0.380','−1.4 [−25.3, 18.7]','0.617','5.8 [−0.7, 13.4]'),
('모션 블러 17 px','0.325','13.4 [−16.8, 36.7]','0.640','2.3 [−8.0, 11.7]')]
T0=607; assert R[T0][0]==71 and R[T0][2][:4]==b' lbt'
lvl=R[T0][1]
end=T0+1
while R[end][1]>lvl: end+=1
cells=[]; j=T0+2
while j<end:
    assert R[j][0]==72; k=j+1
    while k<end and R[k][0]!=72: k+=1
    cells.append(R[j:k]); j=k
assert len(cells)==25
hdr=cells[:5]; tmpl=cells[5:10]
new=[]
for r,row in enumerate(rows,start=1):
    for c,txt in enumerate(row):
        cl=[list(x) for x in tmpl[c]]
        lh=bytearray(cl[0][2]); lh[10:12]=S.pack('<H',r); cl[0][2]=bytes(lh)
        parts=txt.split(' [',1); parts=[parts[0]]+(['['+parts[1]] if len(parts)>1 else [])
        lh=bytearray(cl[0][2]); lh[0:4]=S.pack('<I',len(parts)); cl[0][2]=bytes(lh)
        out=[cl[0]]
        for pi,ptxt in enumerate(parts):
            ph=bytearray(cl[1][2]); body=ptxt.encode('utf-16le')+b'\r\0'
            ph[0:4]=S.pack('<I',(len(body)//2)|(0x80000000 if pi==len(parts)-1 else 0)); ph[16:18]=S.pack('<H',0)
            out+=[[P_HDR,cl[1][1],bytes(ph)],[P_TXT,cl[1][1]+1,body],[P_CS,cl[1][1]+1,S.pack('<II',0,0x28)]]
        new+=out
t=bytearray(R[T0+1][2]); nr=1+len(rows)
t[4:6]=S.pack('<H',nr); t=t[:18]+b''.join(S.pack('<H',5) for _ in range(nr))+t[-4:]
hh=S.unpack('<I',hdr[0][0][2][20:24])[0]; rh=S.unpack('<I',tmpl[0][0][2][20:24])[0]
c=bytearray(R[T0][2]); c[20:24]=S.pack('<I',hh+rh*len(rows))
# table para header (603) lineseg drop
setpara_tbl=R[603]; h=bytearray(R[603][2]); h[16:18]=S.pack('<H',0); R[603][2]=bytes(h)
R[606][0]=None
NEW=R[:T0]+[[71,lvl,bytes(c)],[77,lvl+1,bytes(t)]]+[x for cl in hdr for x in cl]+new+R[end:]
NEW=[x for x in NEW if x[0] is not None]
# strip stale linesegs of all top-level paragraphs after the title block, except picture paragraphs
out=[];cur=None
for x in NEW:
    if x[0]==P_HDR and x[1]==0: cur=x; haspic=False
    out.append(x)
for i,x in enumerate(out):
    if x[0]==P_HDR and x[1]==0 and i>170:
        j=i+1; pic=False
        while j<len(out) and out[j][1]>0:
            if out[j][0]==71 and out[j][2][:4]==b' osg': pic=True
            j+=1
        if pic: continue
        h=bytearray(x[2]); h[16:18]=S.pack('<H',0); x[2]=bytes(h)
        for k in range(i+1,j):
            if out[k][0]==P_LS and out[k][1]==1: out[k][0]=None
NEW=[x for x in out if x[0] is not None]
open('/tmp/claude-0/v2/out/Section1.bin','wb').write(comp(enc(NEW)))
print('ok',len(NEW))
