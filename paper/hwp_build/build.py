import sys,json,struct as S,zlib,io
sys.path.insert(0,'/tmp/claude-0')
from hwplib import recs,enc,comp
import olefile
from PIL import Image
SRC='/tmp/claude-0/hw/form.hwp'; OUT='/tmp/claude-0/build/'
f=olefile.OleFileIO(SRC)
R=recs(zlib.decompress(f.openstream('BodyText/Section1').read(),-15))
EQ=json.load(open('/tmp/claude-0/eqsizes.json'))
P_HDR,P_TXT,P_CS,P_LS,CTRL,LIST,TABLE,EQE=66,67,68,69,71,72,77,88

# ---------- DocInfo: yellow-highlight char shapes, bindata ext -> png
D=recs(zlib.decompress(f.openstream('DocInfo').read(),-15))
idm=list(S.unpack('<18I',D[1][2]))
cs_idx=[i for i,(t,l,p) in enumerate(D) if t==21]
NCS=idm[9]; assert NCS==len(cs_idx)
def yellow(base):
    p=bytearray(D[cs_idx[base]][2]); p[60:64]=bytes.fromhex('ffff0000'); return bytes(p)
CS_YB=NCS; CS_YT=NCS+1   # body 9pt yellow, table 8.48 yellow
newcs=[[21,D[cs_idx[0]][1],yellow(0)],[21,D[cs_idx[0]][1],yellow(5)]]
D=D[:cs_idx[-1]+1]+newcs+D[cs_idx[-1]+1:]
idm[9]+=2; D[1][2]=S.pack('<18I',*idm)
# BIN_DATA id2: bmp -> png
bd=[i for i,(t,l,p) in enumerate(D) if t==18][1]
assert D[bd][2]==bytes.fromhex('01000200030062006d007000')
D[bd][2]=bytes.fromhex('010002000300')+'png'.encode('utf-16le')
open(OUT+'DocInfo.bin','wb').write(comp(enc(D)))

# ---------- helpers
inst=[0x51A00000]
def nid(): inst[0]+=7; return inst[0]
def ext(code,cid):  # 8 wchar extended ctrl
    return S.pack('<H',code)+cid+b'\0'*8+S.pack('<H',code)
class Ctrl:
    def __init__(s,code,cid,recs_fn): s.code=code; s.cid=cid; s.fn=recs_fn
def eqctrl(key,base_level):
    e=EQ[key]; c=bytearray(bytes.fromhex(e['ctrl'])); c[36:40]=S.pack('<I',nid())
    return [[CTRL,base_level,bytes(c)],[EQE,base_level+1,bytes.fromhex(e['eq'])]]
def EQc(key):
    c=Ctrl(11,b'deqe',lambda L: eqctrl(key,L)); c.h=EQ[key]['h']; return c
def para(parts,ps,style=0,cs=0,level=0,last=False,ctrl_mask_extra=0,prefix=b'',prefix_len=0,prefix_mask=0):
    """parts: list of str | (str,cs) | Ctrl"""
    txt=bytearray(prefix); n=0; runs=[]; mask=prefix_mask; children=[]
    def addrun(c):
        if runs and runs[-1][1]==c: return
        if runs and runs[-1][0]==n: runs[-1]=(n,c)
        else: runs.append((n,c))
    if prefix_len: addrun(cs); n=prefix_len
    for p in parts:
        if isinstance(p,Ctrl):
            addrun(cs); txt+=ext(p.code,p.cid); n+=8; mask|=1<<p.code; children+=p.fn(level+1)
        else:
            s,c=(p,cs) if isinstance(p,str) else p
            if not s: continue
            addrun(c); b=s.encode('utf-16le'); txt+=b; n+=len(b)//2
    if not runs: runs=[(0,cs)]
    txt+=b'\r\0'; n+=1
    hdr=S.pack('<IIHBBHHHIH',n|(0x80000000 if last else 0),mask,ps,style,0,len(runs),0,0,0,0)
    out=[[P_HDR,level,hdr]]
    out.append([P_TXT,level+1,bytes(txt)]) if n>1 or prefix_len else None
    out.append([P_CS,level+1,b''.join(S.pack('<II',a,b) for a,b in runs)])
    return out+children
def setlast(rs):
    # mark the last top-level paragraph header (level of first rec) as last
    L=rs[0][1]; idx=max(i for i,(t,l,p) in enumerate(rs) if t==P_HDR and l==L)
    p=bytearray(rs[idx][2]); n=S.unpack('<I',p[:4])[0]|0x80000000; p[:4]=S.pack('<I',n); rs[idx][2]=bytes(p)
    return rs

# ---------- table builder (clone template cell/table format)
TBL_CTRL=R[215][2]; TBL_REC=R[216][2]; CELL_LH=R[217][2]
def rowh(row):
    m=1100
    for cell in row:
        for p in (cell if isinstance(cell,list) else [cell]):
            if isinstance(p,Ctrl) and getattr(p,'h',0): m=max(m,p.h+700)
    return m
def table(rows,widths,header_rows=1,level=1):
    nr,nc=len(rows),len(rows[0]); W=sum(widths); RHS=[rowh(r) for r in rows]
    def fn(L):
        c=bytearray(TBL_CTRL); c[16:20]=S.pack('<I',W); c[20:24]=S.pack('<I',sum(RHS)); c[36:40]=S.pack('<I',nid())
        t=bytearray(TBL_REC[:18])+b''.join(S.pack('<H',nc) for _ in range(nr))+TBL_REC[-4:]
        t[4:6]=S.pack('<H',nr); t[6:8]=S.pack('<H',nc)
        out=[[CTRL,L,bytes(c)],[TABLE,L+1,bytes(t)]]
        for r,row in enumerate(rows):
            for ci,cell in enumerate(row):
                lh=bytearray(CELL_LH); lh[0:4]=S.pack('<I',1); lh[4:8]=S.pack('<I',0x20)
                lh[8:16]=S.pack('<HHHH',ci,r,1,1); lh[16:20]=S.pack('<I',widths[ci]); lh[20:24]=S.pack('<I',RHS[r])
                lh[34:38]=S.pack('<I',widths[ci])
                out.append([LIST,L+1,bytes(lh)])
                parts=cell if isinstance(cell,list) else [cell]
                out+=para(parts,6,6,6 if r<header_rows else 5,level=L+1,last=True)
        return out
    return Ctrl(11,b' lbt',fn)

# ---------- picture (clone template gso, swap size)
im=Image.open('/mnt/project-files/paper/figures/fig1_분석절차.png').convert('RGBA')
bg=Image.new('RGB',im.size,'white'); bg.paste(im,mask=im.split()[3]); bio=io.BytesIO(); bg.save(bio,'PNG',optimize=True)
open(OUT+'BIN0002.png.bin','wb').write(comp(bio.getvalue()))
FW=int(78/25.4*7200); FH=int(FW*im.size[1]/im.size[0])
def picfn(L):
    import os
    if os.environ.get('ORIGPIC'): return [[CTRL,L,R[190][2]],[76,L+1,R[191][2]],[85,L+2,R[192][2]]]
    g=bytearray(R[190][2][:44]); g[16:20]=S.pack('<I',FW); g[20:24]=S.pack('<I',FH); g[36:40]=S.pack('<I',nid())
    desc='그림 1. 전체 분석 절차'.encode('utf-16le'); g+=S.pack('<H',len(desc)//2)+desc
    s=bytearray(R[191][2]); s[20:36]=S.pack('<IIII',FW,FH,FW,FH); s[42:50]=S.pack('<ii',FW//2,FH//2)
    mats=list(S.unpack('<18d',s[52:196])); mats[6]=1.0; mats[10]=1.0; s[52:196]=S.pack('<18d',*mats)
    p=bytearray(R[192][2]); p[12:44]=S.pack('<8i',0,0,FW,0,FW,FH,0,FH); p[44:60]=S.pack('<4i',0,0,FW,FH)
    p[74:78]=S.pack('<I',nid()); p[82:90]=S.pack('<II',FW,FH)
    return [[CTRL,L,bytes(g)],[76,L+1,bytes(s)],[85,L+2,bytes(p)]]
PIC=Ctrl(11,b' osg',picfn)

# ---------- content
Y=lambda s:(s,CS_YB)
IND='  '
def body(*parts): return para([IND,*parts],17,0,0)
def h1(s): return para([s],1,10,9)
def h2(s): return para([s],3,3,0x0b)
def blank(): return para([],1,0,0)
def tcap(s): return para([s],10,5,0x0c)
def tblpara(rows,widths): return para([table(rows,widths)],14,0,0)
def ref(s): return para([s],18,0,0)
TY=lambda s:(s,CS_YT)

B=[]
B+=h1('I. 서 론')
B+=body('교통사고를 신속하게 파악하는 기술은 지능형 교통 시스템의 핵심 요소로, 도로 CCTV 영상에서 딥러닝으로 교통사고를 탐지하는 연구가 진행되어 왔다[1]. 최근에는 도로에 설치된 CCTV 영상에 비전-언어 모델(Vision-Language Model, VLM)을 적용하여, 별도의 학습 없이 사고의 발생 시점과 위치까지 판단하려는 연구가 진행되고 있다[2]. 그러나 실제 CCTV 영상은 원거리 촬영, 저장과 전송을 위한 압축, 차량의 움직임에 따른 모션 블러 등으로 화질이 낮은 경우가 많으며, 공개 CCTV 사고 영상으로 구성된 ACCIDENT 데이터셋에서도 영상의 약 3분의 2가 저화질로 분류되었다[2][3]. 영상 열화가 AI 성능에 미치는 영향은 주로 객체 탐지를 중심으로 연구되어 왔으며[3][4][5], 여러 프레임의 변화를 읽어야 하는 사고 시점·위치 판단에서의 영향은 아직 충분히 알려져 있지 않다.')
B+=body('이에 본 연구는 ACCIDENT 벤치마크[2]의 실제 CCTV 사고 영상에 해상도 저하, H.264 압축, 모션 블러를 단계적으로 적용하고, Molmo-7B-D[6]의 사고 시점·위치 판단 성능이 열화에 따라 어떻게 달라지는지 원본 대비 상대 하락률로 비교·분석한다. 이를 통해 어떤 판단 능력이 어떤 열화에 더 취약한지 확인하고, CCTV 기반 사고 탐지 시스템의 화질 관리 방향을 제시하고자 한다.')
B+=blank()
B+=h1('II. 관련연구')
B+=h2('2.1 CCTV 교통사고 벤치마크와 비전-언어 모델')
B+=body('ACCIDENT[2]는 실제 도로 CCTV에서 수집한 사고 영상 2,027개와 합성 영상 2,211개로 구성된 벤치마크로, 사고의 발생 시점(When), 위치(Where), 유형(What)을 판단하는 세 가지 과제를 정의하였다. 각 과제의 정답은 여러 주석자의 표시를 평균하여 정하고, 예측은 정답과의 차이가 클수록 점수가 부드럽게 감소하는 가우시안 유사도로 평가한다. 별도의 학습 없이 사용한 VLM 중에서는 Molmo-7B-D가 시점 0.343, 위치 0.596으로 가장 높은 성능을 보였다[2]. Molmo[6]는 이미지 속 대상을 좌표로 가리키는(pointing) 데이터로 학습된 공개 VLM으로, 본 연구에서도 별도의 학습 없이 사고 시점과 위치 판단에 사용한다.')
B+=h2('2.2 영상 열화와 AI 성능')
B+=body('영상 열화가 AI 성능에 미치는 영향은 주로 객체 탐지를 대상으로 분석되어 왔다. O’Byrne 등[3]은 실제 감시 영상을 H.264 코덱의 CRF(Constant Rate Factor) 22~47로 압축하여 객체 탐지 성능을 측정하였고, CRF 42 이상에서 성능이 뚜렷하게 낮아짐을 보였다. Cai 등[4]은 모션 블러를 포함한 여러 악조건에서 차량 탐지 모델의 강건성을 평가하면서 원본 대비 성능 손실률을 지표로 사용하였으며, 윤영두·김호[5]는 해상도 축소와 압축을 함께 적용하여 탐지 신뢰도가 비선형적으로 저하되는 구간을 분석하였다. 권오설[7]은 저해상도 영상에서 세부 정보가 손실되어 차량 검출 정확도가 낮아지는 문제를 다루었다. Poyser 등[8]은 행동 인식에서 압축이 강해질 때 프레임 간 움직임 정보를 사용하는 경로의 성능이 외형 정보를 사용하는 경로보다 크게 떨어짐을 보고하여, 열화의 영향이 판단에 필요한 정보의 종류에 따라 달라질 수 있음을 보여주었다.')
B+=body('모션 블러는 카메라의 노출 시간 동안 피사체가 이동한 거리만큼 상이 번지는 현상이다. 따라서 블러 길이 ',EQc('L'),'(픽셀)은 차량 속도와 노출 시간, 카메라의 공간 해상도로부터 식 (1)과 같이 근사할 수 있다.')
B+=para([EQc('E1'),'                    (1)'],14,0,0)
B+=body('여기서 ',EQc('v'),'는 차량 속도(m/s), ',EQc('te'),'는 노출 시간(s), ',EQc('d'),'는 픽셀 하나가 나타내는 도로 위의 실제 거리(m)이다. 본 연구는 식 (1)을 이용하여 실제 차량 속도에 대응하는 모션 블러 단계를 정한다.')
B+=blank()
B+=h1('III. 연구 방법')
B+=body('본 연구의 전체 분석 절차는 (그림 1)과 같다. 실제 CCTV 사고 영상에 열화를 적용하고, 각 조건에서 Molmo-7B-D의 사고 시점·위치 판단 성능을 측정한 뒤 원본 대비 하락률로 비교한다.')
_pp=para([PIC],14,0,0)
import os
if True:
    h=bytearray(_pp[0][2]); h[16:18]=S.pack('<H',1); _pp[0][2]=bytes(h); ls=bytearray(R[189][2]); ls[4:8]=S.pack('<i',0); ls[8:20]=S.pack('<iii',FH,FH,int(FH*0.85)); _pp.insert(3,[P_LS,1,bytes(ls)])
B+=_pp
B+=para(['(그림 1) 전체 분석 절차'],5,5,0x1a)
B+=h2('3.1 데이터셋과 모델')
B+=body('실험에는 ACCIDENT의 실제 CCTV 사고 영상 중 무작위로 추출한 50개를 사용한다. 모델은 Molmo-7B-D (allenai/Molmo-7B-D-0924)를 별도의 학습 없이 사용하며, 질의 문장과 추론 절차는 ACCIDENT 공식 코드를 따른다. 시점 판단에서는 영상을 0.5초 간격 프레임으로 나누어 각 프레임에 사고 여부를 묻고, 처음으로 사고라고 답한 프레임의 시각을 예측 시점으로 한다. 위치 판단에서는 정답 사고 프레임 한 장을 주고 사고 지점을 점으로 가리키게 한다. 위치 판단에 정답 프레임을 주는 오라클 보조 방식[2]은 시점 판단의 오류가 위치 점수에 섞이지 않도록 하기 위함이다.')
B+=h2('3.2 열화 조건')
B+=body('열화는 카메라 촬영과 영상 전송 과정에서 발생하며 통제하여 재현할 수 있는 해상도 저하, H.264 압축, 모션 블러의 세 가지로 하고, 각각 3단계를 적용한다(표 1). 해상도 저하는 프레임을 축소한 뒤 원래 크기로 다시 확대하고, 압축은 ffmpeg의 libx264로 영상을 재인코딩하며, 모션 블러는 식 (1)로 구한 길이의 수평 선형 커널을 각 프레임에 적용한다. 모션 블러 단계는 차량 속도 30·60·90 km/h, 노출 시간 1/30 s, 픽셀당 거리 0.05 m를 가정하여 정하였다. 원본을 포함한 10개 조건에서 같은 영상을 평가한다.')
B+=tcap(' (표 1) 열화 조건과 단계')
B+=tblpara([['열화 (단위)','1단계','2단계','3단계','근거'],
 ['해상도 저하 (축소 배율)','1/2','1/4','1/8','[5][7]'],
 ['H.264 압축 (CRF)','37','42','47','[3]'],
 ['모션 블러 (길이, px)','6','11','17','식 (1)']],[8600,3500,3500,3500,4600])
B+=h2('3.3 평가 지표')
B+=body('시점과 위치 판단은 ACCIDENT의 평가 방식[2]에 따라 가우시안 유사도로 측정하고, 열화의 영향은 원본 대비 상대 하락률(Relative Performance Drop, RPD)로 비교한다(표 2). RPD는 원본 성능이 서로 다른 두 판단 능력을 같은 기준에서 비교하기 위한 것으로, 강건성 평가 연구[4]의 성능 손실률과 같은 형태이다. 조건 간 차이는 같은 영상의 원본·열화 결과를 짝지은 부트스트랩으로 95% 신뢰구간을 구하여 확인한다.')
B+=tcap(' (표 2) 평가 지표')
B+=tblpara([['과제','지표','정의'],
 ['시점',['시간 유사도 ',EQc('Tt')],[EQc('T2a')]],
 ['위치',['공간 유사도 ',EQc('Ts')],[EQc('T2b')]],
 ['비교','상대 하락률 RPD',[EQc('T2c'),' (%)']]],[3400,6000,14300])
B+=blank()
B+=h1('IV. 실험 결과')
B+=h2('4.1 원본 성능 재현')
B+=body('열화를 적용하기 전에 원본 영상에서 성능을 확인하였다(표 3). 무작위로 추출한 영상 20개에서 Molmo-7B-D는 시점 0.465, 위치 0.670으로 단순 기준선(영상 중앙 시각, 화면 중앙 좌표)보다 크게 높았으며, ACCIDENT에서 보고된 값과 비슷한 수준이었다. 영상별 점수가 0 또는 1에 가깝게 나뉘는 경향이 있어 표본이 작을 때 평균이 보고값과 차이를 보일 수 있다. 시점 판단에서 사고를 한 번도 탐지하지 못한 영상은 10%였다.')
B+=tcap(' (표 3) 원본 영상에서의 성능')
B+=tblpara([['구분','영상 수',['시점 ',EQc('Tt')],['위치 ',EQc('Ts')]],
 ['단순 기준선[2]','2,027','0.190','0.250'],
 ['Molmo-7B-D 보고값[2]','2,027','0.343','0.596'],
 ['Molmo-7B-D 재현 (본 연구)','20','0.465','0.670']],[10300,4200,4600,4600])
B+=h2('4.2 열화 조건별 성능 비교')
B+=body(Y('(작성 예정) 영상 50개로 10개 조건을 실행한 뒤, 표 4의 조건별 점수와 하락률, 열화 단계에 따른 성능 변화 그래프(그림 2)를 바탕으로 어떤 판단 능력이 어떤 열화에 더 취약한지 서술한다.'))
B+=tcap(' (표 4) 열화 조건별 성능과 원본 대비 하락률')
B+=tblpara([['조건',[EQc('Tt')],[EQc('Trt'),' (%)'],[EQc('Ts')],[EQc('Trs'),' (%)']],
 ['원본','–','–','–','–'],
 ['해상도 1/2 · 1/4 · 1/8','–','–','–','–'],
 ['H.264 CRF 37 · 42 · 47','–','–','–','–'],
 ['모션 블러 6 · 11 · 17 px','–','–','–','–']],[8900,3200,4600,3200,4600])
B+=blank()
B+=h1('V. 결 론')
B+=body('본 논문은 실제 CCTV 사고 영상에 해상도 저하, H.264 압축, 모션 블러를 단계적으로 적용하여, VLM의 사고 시점·위치 판단 성능이 열화에 따라 어떻게 저하되는지 분석하는 평가 체계를 제시하였다. 원본 영상에서는 기존 보고 수준의 성능을 재현하였으며, ',Y('(열화 결과: 어떤 판단이 어떤 열화에 가장 취약한지 1~2문장)'),'. 이는 CCTV 기반 사고 탐지 시스템에서 관리해야 할 화질 조건을 판단 능력별로 제시한다는 점에서 의미가 있다. 다만 본 연구는 하나의 모델과 제한된 수의 영상을 사용하였고, 열화를 합성으로 재현하였다는 한계가 있다. 향후에는 다른 VLM과 더 많은 영상으로 분석을 확장하고, 열화에 강건한 학습 및 복원 기법과 합성 데이터를 활용한 학습 방향을 연구할 계획이다.')
B+=blank()
B+=para(['참 고 문 헌'],15,0,0x12)
REFS=open('/tmp/claude-0/build/refs.txt',encoding='utf-8').read().strip().split('\n')
for r in REFS:
    if r.strip(): B+=ref(r.strip())
setlast(B)

# ---------- title table edits (para 0 kept)
H=[list(x) for x in R[:163]]
def cellpara(i_hdr,i_end,parts,cs,last):
    old=H[i_hdr][2]; ps,style=S.unpack('<HB',old[8:11])
    L=H[i_hdr][1]
    new=para(parts,ps,style,cs,level=L,last=last)
    return new
def replace_range(a,b,new):  # inclusive indices in original numbering -> handled via dict
    REPL[a]=(b,new)
REPL={}
# title (keeps 'head' ctrl at start): prefix = original first 16 bytes of text
t=H[21][2]; pre=t[:16]
ps,style=S.unpack('<HB',H[20][2][8:11])
new=para(['CCTV 영상 열화에 따른 교통사고 탐지 AI의 성능 저하 및 취약성 분석'],ps,style,0x0e,level=H[20][1],last=True)
REPL[20]=(29,new)
# move the running-header ctrl ('head') into the empty first cell of the same row
ps0,st0=S.unpack('<HB',H[16][2][8:11])
cell0=para([],ps0,st0,4,level=H[16][1],last=True,prefix=pre,prefix_len=8,prefix_mask=1<<16)
REPL[16]=(18,cell0+[list(x) for x in H[24:30]])   # header,text,cs ; children (head ctrl 24-29) kept
au=[('이우석, 안한석*, 안동현*',False),('강남대학교 데이터사이언스학부, *강남대학교 인공지능학부',False),('kidde04@kangnam.ac.kr, *hanseogan@kangnam.ac.kr, *bill207@kangnam.ac.kr',True)]
blk=[]
for (s,last),hi in zip(au,(51,55,59)):
    ps,style=S.unpack('<HB',H[hi][2][8:11]); blk+=para([s],ps,style,3,level=H[hi][1],last=last)
REPL[51]=(62,blk)
ps,style=S.unpack('<HB',H[84][2][8:11])
REPL[84]=(87,para(['Analysis of Performance Degradation and Vulnerability of Traffic Accident Detection AI under CCTV Video Degradation'],ps,style,0x0d,level=H[84][1],last=True))
blk=[]
for (s,last),hi in zip([('Lee Woo Seok, An Han Seok*, Ahn Dong Hyun*',False),('Dept. of Data Science, Kangnam Univ., *Dept. of Artificial Intelligence, Kangnam Univ.',True)],(109,113)):
    ps,style=S.unpack('<HB',H[hi][2][8:11]); blk+=para([s],ps,style,3,level=H[hi][1],last=last)
REPL[109]=(116,blk)
# abstract (keeps pgnp ctrl at start)
ab=H[143][2]; pre=ab[:16]; ps,style=S.unpack('<HB',H[142][2][8:11])
abs_txt=' 본 논문은 CCTV 영상의 화질 저하가 비전-언어 모델(Vision-Language Model, VLM)의 교통사고 판단 능력에 미치는 영향을 분석한다. 실제 CCTV 사고 영상으로 구성된 ACCIDENT 벤치마크에 해상도 저하, H.264 압축, 모션 블러(Motion Blur)를 각각 3단계로 적용하고, Molmo-7B-D를 별도의 학습 없이 사용하여 사고의 발생 시점과 위치를 판단하는 성능을 측정한다. 각 조건의 성능은 원본 대비 상대 하락률로 비교하여 어떤 판단 능력이 어떤 열화에 더 취약한지 확인한다. 원본 영상 20개에 대한 실험에서 시점 0.465, 위치 0.670으로 기존 보고 수준의 성능을 재현하였다. '
new=para([abs_txt,Y('(열화 조건별 주요 결과 1문장 추가 예정)')],ps,style,0,level=H[142][1],last=True,prefix=pre,prefix_len=8,prefix_mask=1<<21)
REPL[142]=(145,new[:3])
def seth(i,newh):
    p=bytearray(H[i][2]); old=S.unpack('<I',p[20:24])[0]; p[20:24]=S.pack('<I',newh); H[i][2]=bytes(p); return newh-old
dh=seth(19,5600)+seth(83,7000)+seth(108,4200)
p=bytearray(H[13][2]); p[20:24]=S.pack('<I',S.unpack('<I',p[20:24])[0]+dh); H[13][2]=bytes(p)
ps,style=S.unpack('<HB',H[138][2][8:11])
REPL[138]=(141,para(['요   약'],ps,style,0x11,level=H[138][1]))
OUTR=[]; i=0
while i<len(H):
    if i in REPL and REPL[i] is not None:
        b,new=REPL[i]; OUTR+=new; i=b+1
    else: OUTR.append(H[i]); i+=1
OUTR+=B
open(OUT+'Section1.bin','wb').write(comp(enc(OUTR)))
# PrvText
print('ok', len(OUTR))
