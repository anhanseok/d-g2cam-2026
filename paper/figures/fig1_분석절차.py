import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
plt.rcParams['font.family']='WenQuanYi Zen Hei'
W,H=3.4,3.45
K=3.45/4.6
fig=plt.figure(figsize=(W,H),dpi=300); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,4.6); ax.axis('off')
def box(x,y,w,h,title,sub=None,fc='#ffffff',ec='#333333',fs=7.2):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.05',fc=fc,ec=ec,lw=0.8))
    if sub:
        ax.text(x+w/2,y+h-0.06,title,ha='center',va='top',fontsize=fs,weight='bold')
        ax.text(x+w/2,y+(h-0.2)/2,sub,ha='center',va='center',fontsize=fs-1.2,color='#333',linespacing=1.25)
    else:
        ax.text(x+w/2,y+h/2,title,ha='center',va='center',fontsize=fs,weight='bold')
def arrow(x1,y1,x2,y2):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='-|>',lw=0.8,color='#333',mutation_scale=7))
m=0.12; fw=W-2*m
# 1 data
box(m,4.05,fw,0.45,'① 입력 데이터','ACCIDENT 실제 CCTV 사고 영상 (정답 시점·사고 영역)',fc='#eef3fa')
arrow(W/2,4.05,W/2,3.88)
# 2 degradation
y2=3.0; h2=0.86
ax.add_patch(FancyBboxPatch((m,y2),fw,h2,boxstyle='round,pad=0.02,rounding_size=0.05',fc='#fdf3e7',ec='#333',lw=0.8))
ax.text(W/2,y2+h2-0.13,'② 열화 적용 (원본 + 3종 × 3단계 = 10조건)',ha='center',va='center',fontsize=7.2,weight='bold')
cw=(fw-0.32)/4; labels=[('원본','열화 없음'),('해상도 저하','1/2 · 1/4 · 1/8'),('H.264 압축','CRF 3단계'),('모션 블러','식 (1) 3단계')]
for i,(a,b) in enumerate(labels):
    x=m+0.06+i*(cw+0.067)
    box(x,y2+0.08,cw,0.5,a,b,fc='#ffffff',fs=6.4)
arrow(W/2,3.0,W/2,2.83)
# 3 model
box(m,2.4,fw,0.43,'③ Molmo-7B-D (zero-shot)','ACCIDENT 공식 질의·추론 절차',fc='#eef7ee')
# split
hw=(fw-0.12)/2
arrow(m+hw/2,2.4,m+hw/2,2.22); arrow(W-m-hw/2,2.4,W-m-hw/2,2.22)
box(m,1.6,hw,0.62,'시점(When) 판단','0.5초 간격 프레임마다\n사고 여부 질의 →\n첫 "Yes" 시각',fs=6.6)
box(W-m-hw,1.6,hw,0.62,'위치(Where) 판단','정답 사고 프레임에서\n사고 지점을 점으로 지시\n(오라클 보조)',fs=6.6)
arrow(m+hw/2,1.6,m+hw/2,1.43); arrow(W-m-hw/2,1.6,W-m-hw/2,1.43)
box(m,1.05,hw,0.38,'시간 유사도 T','가우시안, σt = 1초',fs=6.6)
box(W-m-hw,1.05,hw,0.38,'공간 유사도 S','2차원 가우시안',fs=6.6)
arrow(m+hw/2,1.05,W/2-0.05,0.86); arrow(W-m-hw/2,1.05,W/2+0.05,0.86)
box(m,0.12,fw,0.74,'④ 비교·분석','조건별 원본 대비 상대 하락률(RPD)\n영상 단위 짝지은 부트스트랩 95% 신뢰구간\n→ 어떤 판단이 어떤 열화에 더 취약한가',fc='#f3eefa')
fig.savefig('/mnt/project-files/paper/figures/fig1_분석절차.png',dpi=300)
