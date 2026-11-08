import re, sys
from docx import Document
from docx.shared import Pt, Mm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
OUT=sys.argv[1]; FIG=sys.argv[2]
MY='바탕'; GO='맑은 고딕'; LAT='Times New Roman'
d=Document()
sec=d.sections[0]
sec.page_width,sec.page_height=Mm(210),Mm(297)
for s in [sec]:
    s.top_margin=s.bottom_margin=Mm(12); s.left_margin=s.right_margin=Mm(15)
    s.header_distance=s.footer_distance=Mm(12)
st=d.styles['Normal']; st.font.name=LAT; st.font.size=Pt(9)
st.element.rPr.rFonts.set(qn('w:eastAsia'),MY)
pf=st.paragraph_format; pf.space_before=Pt(0); pf.space_after=Pt(0); pf.line_spacing=1.5
def setfont(r,ea=MY,lat=LAT):
    r.font.name=lat; rp=r._element.get_or_add_rPr(); rf=rp.find(qn('w:rFonts'))
    if rf is None: rf=OxmlElement('w:rFonts'); rp.insert(0,rf)
    rf.set(qn('w:eastAsia'),ea); rf.set(qn('w:ascii'),lat); rf.set(qn('w:hAnsi'),lat)
def rich(p,s,size=9,bold=False,ea=MY,lat=LAT):
    hl=False
    for t in re.split(r'(\[\[|\]\]|_\{[^}]*\}|\^\{[^}]*\}|\*[^*]+\*)',s):
        if not t: continue
        if t=='[[': hl=True; continue
        if t==']]': hl=False; continue
        sub=sup=it=False
        if t.startswith('_{'): sub=True; t=t[2:-1]
        elif t.startswith('^{'): sup=True; t=t[2:-1]
        elif t.startswith('*') and len(t)>2: it=True; t=t[1:-1]
        r=p.add_run(t); setfont(r,ea,lat); r.font.size=Pt(size); r.bold=bold
        r.font.subscript=sub or None; r.font.superscript=sup or None; r.italic=it or None
        if hl: r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    return p
def para(s,size=9,bold=False,align=None,indent=True,ls=1.5,before=0,after=0,ea=MY):
    p=d.add_paragraph(); rich(p,s,size,bold,ea)
    f=p.paragraph_format; f.line_spacing=ls; f.space_before=Pt(before); f.space_after=Pt(after)
    if align is not None: p.alignment=align
    else: p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    if indent and align is None: f.first_line_indent=Pt(9)
    return p
C=WD_ALIGN_PARAGRAPH.CENTER
body=lambda s: para(s)
def h1(s): p=para(s,10,True,WD_ALIGN_PARAGRAPH.LEFT,before=8,after=3); p.paragraph_format.keep_with_next=True
def h2(s): p=para(s,9,True,WD_ALIGN_PARAGRAPH.LEFT,before=4,after=1); p.paragraph_format.keep_with_next=True
def cols(section,n,space_mm=10):
    sp=section._sectPr; c=sp.find(qn('w:cols'))
    if c is None: c=OxmlElement('w:cols'); sp.append(c)
    c.set(qn('w:num'),str(n)); c.set(qn('w:space'),str(int(space_mm/25.4*1440)))
def cell_border(cell,**kw):
    tcPr=cell._tc.get_or_add_tcPr(); b=OxmlElement('w:tcBorders')
    for k,v in kw.items():
        e=OxmlElement(f'w:{k}'); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),str(v)); e.set(qn('w:color'),'000000'); b.append(e)
    tcPr.append(b)
def table(cap,rows,widths_mm):
    p=para(cap,9,False,C,before=6,after=2,ea=GO); p.paragraph_format.keep_with_next=True
    t=d.add_table(rows=len(rows),cols=len(rows[0])); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    tblPr=t._tbl.tblPr; lay=OxmlElement('w:tblLayout'); lay.set(qn('w:type'),'fixed'); tblPr.append(lay)
    tw=OxmlElement('w:tblW'); tw.set(qn('w:w'),str(int(sum(widths_mm)/25.4*1440))); tw.set(qn('w:type'),'dxa')
    old=tblPr.find(qn('w:tblW'))
    if old is not None: tblPr.remove(old)
    tblPr.append(tw)
    for gc,w in zip(t._tbl.tblGrid.findall(qn('w:gridCol')),widths_mm): gc.set(qn('w:w'),str(int(w/25.4*1440)))
    for j,w in enumerate(widths_mm): t.columns[j].width=Mm(w)
    for i,row in enumerate(rows):
        for j,txt in enumerate(row):
            c=t.cell(i,j); c.width=Mm(widths_mm[j]); c.text=''
            q=c.paragraphs[0]; rich(q,txt,8,bold=(i==0)); q.alignment=C
            q.paragraph_format.line_spacing=1.15
            if i<len(rows)-1: q.paragraph_format.keep_with_next=True
            if i==0: cell_border(c,top=8,bottom=4)
            if i==len(rows)-1: cell_border(c,bottom=8)
    sp=d.add_paragraph(); sp.paragraph_format.space_after=Pt(4); sp.paragraph_format.line_spacing=1.0
    return t
# header
hp=sec.header.paragraphs[0]; rich(hp,'2026년도 (사)융복합지식학회 추계학술발표대회 논문집',8); hp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
# ---- title block (1 column)
para('CCTV 영상 열화에 따른 교통사고 탐지 AI의 성능 저하 및 취약성 분석',16,True,C,ls=1.2,after=6)
para('이우석, 안한석^{*}, 안동현^{*}',10,False,C,ls=1.3)
para('강남대학교 데이터사이언스학부, ^{*}강남대학교 인공지능학부',10,False,C,ls=1.3)
para('kidde04@kangnam.ac.kr, ^{*}hanseogan@kangnam.ac.kr, ^{*}bill207@kangnam.ac.kr',10,False,C,ls=1.3,after=8)
para('Analysis of Performance Degradation and Vulnerability of Traffic Accident Detection AI under CCTV Video Degradation',14,True,C,ls=1.2,after=4)
para('Lee Woo Seok, An Han Seok^{*}, Ahn Dong Hyun^{*}',10,False,C,ls=1.3)
para('Dept. of Data Science, Kangnam Univ., ^{*}Dept. of Artificial Intelligence, Kangnam Univ.',10,False,C,ls=1.3,after=10)
para('요   약',11,False,C,ls=1.3,after=3)
ab=para('본 논문은 CCTV 영상의 화질 저하가 비전-언어 모델(Vision-Language Model, VLM)의 교통사고 판단 능력에 미치는 영향을 분석한다. 실제 CCTV 사고 영상으로 구성된 ACCIDENT 벤치마크에 해상도 저하, H.264 압축, 모션 블러(Motion Blur)를 각각 3단계로 적용하고, Molmo-7B-D를 별도의 학습 없이 사용하여 사고의 발생 시점과 위치를 판단하는 성능을 측정한다. 각 조건의 성능은 원본 대비 상대 하락률로 비교하여 어떤 판단 능력이 어떤 열화에 더 취약한지 확인한다. 원본 영상 20개에 대한 실험에서 시점 0.465, 위치 0.670으로 기존 보고 수준의 성능을 재현하였다. [[(열화 조건별 주요 결과 1문장 추가 예정)]]',9,ls=1.3,after=6)
ab.paragraph_format.left_indent=Mm(8); ab.paragraph_format.right_indent=Mm(8)
# ---- body (2 columns)
s2=d.add_section(WD_SECTION.CONTINUOUS); cols(s2,2,10)
h1('I. 서 론')
body('교통사고를 신속하게 파악하는 기술은 지능형 교통 시스템의 핵심 요소로, 도로 CCTV 영상에서 딥러닝으로 교통사고를 탐지하는 연구가 진행되어 왔다[1]. 최근에는 도로에 설치된 CCTV 영상에 비전-언어 모델(Vision-Language Model, VLM)을 적용하여, 별도의 학습 없이 사고의 발생 시점과 위치까지 판단하려는 연구가 진행되고 있다[2]. 그러나 실제 CCTV 영상은 원거리 촬영, 저장과 전송을 위한 압축, 차량의 움직임에 따른 모션 블러 등으로 화질이 낮은 경우가 많으며, 공개 CCTV 사고 영상으로 구성된 ACCIDENT 데이터셋에서도 영상의 약 3분의 2가 저화질로 분류되었다[2][3]. 영상 열화가 AI 성능에 미치는 영향은 주로 객체 탐지를 중심으로 연구되어 왔으며[3][4][5], 여러 프레임의 변화를 읽어야 하는 사고 시점·위치 판단에서의 영향은 아직 충분히 알려져 있지 않다.')
body('이에 본 연구는 ACCIDENT 벤치마크[2]의 실제 CCTV 사고 영상에 해상도 저하, H.264 압축, 모션 블러를 단계적으로 적용하고, Molmo-7B-D[6]의 사고 시점·위치 판단 성능이 열화에 따라 어떻게 달라지는지 원본 대비 상대 하락률로 비교·분석한다. 이를 통해 어떤 판단 능력이 어떤 열화에 더 취약한지 확인하고, CCTV 기반 사고 탐지 시스템의 화질 관리 방향을 제시하고자 한다.')
h1('II. 관련연구')
h2('2.1 CCTV 교통사고 벤치마크와 비전-언어 모델')
body('ACCIDENT[2]는 실제 도로 CCTV에서 수집한 사고 영상 2,027개와 합성 영상 2,211개로 구성된 벤치마크로, 사고의 발생 시점(When), 위치(Where), 유형(What)을 판단하는 세 가지 과제를 정의하였다. 각 과제의 정답은 여러 주석자의 표시를 평균하여 정하고, 예측은 정답과의 차이가 클수록 점수가 부드럽게 감소하는 가우시안 유사도로 평가한다. 별도의 학습 없이 사용한 VLM 중에서는 Molmo-7B-D가 시점 0.343, 위치 0.596으로 가장 높은 성능을 보였다[2]. Molmo[6]는 이미지 속 대상을 좌표로 가리키는(pointing) 데이터로 학습된 공개 VLM으로, 본 연구에서도 별도의 학습 없이 사고 시점과 위치 판단에 사용한다.')
h2('2.2 영상 열화와 AI 성능')
body('영상 열화가 AI 성능에 미치는 영향은 주로 객체 탐지를 대상으로 분석되어 왔다. O’Byrne 등[3]은 실제 감시 영상을 H.264 코덱의 CRF(Constant Rate Factor) 22~47로 압축하여 객체 탐지 성능을 측정하였고, CRF 42 이상에서 성능이 뚜렷하게 낮아짐을 보였다. Cai 등[4]은 모션 블러를 포함한 여러 악조건에서 차량 탐지 모델의 강건성을 평가하면서 원본 대비 성능 손실률을 지표로 사용하였으며, 윤영두·김호[5]는 해상도 축소와 압축을 함께 적용하여 탐지 신뢰도가 비선형적으로 저하되는 구간을 분석하였다. 권오설[7]은 저해상도 영상에서 세부 정보가 손실되어 차량 검출 정확도가 낮아지는 문제를 다루었다. Poyser 등[8]은 행동 인식에서 압축이 강해질 때 프레임 간 움직임 정보를 사용하는 경로의 성능이 외형 정보를 사용하는 경로보다 크게 떨어짐을 보고하여, 열화의 영향이 판단에 필요한 정보의 종류에 따라 달라질 수 있음을 보여주었다.')
body('모션 블러는 카메라의 노출 시간 동안 피사체가 이동한 거리만큼 상이 번지는 현상이다. 따라서 블러 길이 *L*(픽셀)은 차량 속도와 노출 시간, 카메라의 공간 해상도로부터 식 (1)과 같이 근사할 수 있다.')
eq=d.add_paragraph(); eq.paragraph_format.space_before=Pt(4); eq.paragraph_format.space_after=Pt(4)
ts=eq.paragraph_format.tab_stops; ts.add_tab_stop(Mm(42.5),WD_TAB_ALIGNMENT.CENTER); ts.add_tab_stop(Mm(85),WD_TAB_ALIGNMENT.RIGHT)
rich(eq,'\t*L* = *v* · *t*_{e} / *d*\t(1)')
p=para('여기서 *v*는 차량 속도(m/s), *t*_{e}는 노출 시간(s), *d*는 픽셀 하나가 나타내는 도로 위의 실제 거리(m)이다. 본 연구는 식 (1)을 이용하여 실제 차량 속도에 대응하는 모션 블러 단계를 정한다.',indent=False)
h1('III. 연구 방법')
body('본 연구의 전체 분석 절차는 (그림 1)과 같다. 실제 CCTV 사고 영상에 열화를 적용하고, 각 조건에서 Molmo-7B-D의 사고 시점·위치 판단 성능을 측정한 뒤 원본 대비 하락률로 비교한다.')
fp=d.add_paragraph(); fp.alignment=C; fp.paragraph_format.space_before=Pt(4); fp.paragraph_format.keep_with_next=True; fp.paragraph_format.line_spacing=1.0
fp.add_run().add_picture(FIG,width=Mm(82))
para('(그림 1) 전체 분석 절차',9,False,C,ls=1.3,after=4,ea=GO)
h2('3.1 데이터셋과 모델')
body('실험에는 ACCIDENT의 실제 CCTV 사고 영상 중 무작위로 추출한 50개를 사용한다. 모델은 Molmo-7B-D (allenai/Molmo-7B-D-0924)를 별도의 학습 없이 사용하며, 질의 문장과 추론 절차는 ACCIDENT 공식 코드를 따른다. 시점 판단에서는 영상을 0.5초 간격 프레임으로 나누어 각 프레임에 사고 여부를 묻고, 처음으로 사고라고 답한 프레임의 시각을 예측 시점으로 한다. 위치 판단에서는 정답 사고 프레임 한 장을 주고 사고 지점을 점으로 가리키게 한다. 위치 판단에 정답 프레임을 주는 오라클 보조 방식[2]은 시점 판단의 오류가 위치 점수에 섞이지 않도록 하기 위함이다.')
h2('3.2 열화 조건')
body('열화는 카메라 촬영과 영상 전송 과정에서 발생하며 통제하여 재현할 수 있는 해상도 저하, H.264 압축, 모션 블러의 세 가지로 하고, 각각 3단계를 적용한다(표 1). 해상도 저하는 프레임을 축소한 뒤 원래 크기로 다시 확대하고, 압축은 ffmpeg의 libx264로 영상을 재인코딩하며, 모션 블러는 식 (1)로 구한 길이의 수평 선형 커널을 각 프레임에 적용한다. 모션 블러 단계는 차량 속도 30·60·90 km/h, 노출 시간 1/30 s, 픽셀당 거리 0.05 m를 가정하여 정하였다. 원본을 포함한 10개 조건에서 같은 영상을 평가한다.')
table('(표 1) 열화 조건과 단계',[
 ['열화 (단위)','1단계','2단계','3단계','근거'],
 ['해상도 저하 (축소 배율)','1/2','1/4','1/8','[5][7]'],
 ['H.264 압축 (CRF)','37','42','47','[3]'],
 ['모션 블러 (길이, px)','6','11','17','식 (1)'],
],[32,12,12,12,12])
h2('3.3 평가 지표')
body('시점과 위치 판단은 ACCIDENT의 평가 방식[2]에 따라 가우시안 유사도로 측정하고, 열화의 영향은 원본 대비 상대 하락률(Relative Performance Drop, RPD)로 비교한다(표 2). RPD는 원본 성능이 서로 다른 두 판단 능력을 같은 기준에서 비교하기 위한 것으로, 강건성 평가 연구[4]의 성능 손실률과 같은 형태이다. 조건 간 차이는 같은 영상의 원본·열화 결과를 짝지은 부트스트랩으로 95% 신뢰구간을 구하여 확인한다.')
table('(표 2) 평가 지표',[
 ['과제','지표','정의'],
 ['시점','시간 유사도 *T*','exp(−(*t̂* − *t*^{*})^{2} / 2*σ*_{t}^{2}), *σ*_{t} = 1 s'],
 ['위치','공간 유사도 *S*','exp(−Δ*x*^{2} / 2*σ*_{x}^{2} − Δ*y*^{2} / 2*σ*_{y}^{2})'],
 ['비교','상대 하락률 RPD','(*P*_{원본} − *P*_{열화}) / *P*_{원본} × 100 (%)'],
],[10,22,48])
h1('IV. 실험 결과')
h2('4.1 원본 성능 재현')
body('열화를 적용하기 전에 원본 영상에서 성능을 확인하였다(표 3). 무작위로 추출한 영상 20개에서 Molmo-7B-D는 시점 0.465, 위치 0.670으로 단순 기준선(영상 중앙 시각, 화면 중앙 좌표)보다 크게 높았으며, ACCIDENT에서 보고된 값과 비슷한 수준이었다. 영상별 점수가 0 또는 1에 가깝게 나뉘는 경향이 있어 표본이 작을 때 평균이 보고값과 차이를 보일 수 있다. 시점 판단에서 사고를 한 번도 탐지하지 못한 영상은 10%였다.')
table('(표 3) 원본 영상에서의 성능',[
 ['구분','영상 수','시점 *T*','위치 *S*'],
 ['단순 기준선[2]','2,027','0.190','0.250'],
 ['Molmo-7B-D 보고값[2]','2,027','0.343','0.596'],
 ['Molmo-7B-D 재현 (본 연구)','20','0.465','0.670'],
],[36,14,14,14])
h2('4.2 열화 조건별 성능 비교')
body('[[(작성 예정) 영상 50개로 10개 조건을 실행한 뒤, 표 4의 조건별 점수와 하락률, 열화 단계에 따른 성능 변화 그래프(그림 2)를 바탕으로 어떤 판단 능력이 어떤 열화에 더 취약한지 서술한다.]]')
table('(표 4) 열화 조건별 성능과 원본 대비 하락률',[
 ['조건','*T*','RPD_{T} (%)','*S*','RPD_{S} (%)'],
 ['원본','–','–','–','–'],
 ['해상도 1/2 · 1/4 · 1/8','–','–','–','–'],
 ['H.264 CRF 37 · 42 · 47','–','–','–','–'],
 ['모션 블러 6 · 11 · 17 px','–','–','–','–'],
],[33,10,14,10,14])
h1('V. 결 론')
body('본 논문은 실제 CCTV 사고 영상에 해상도 저하, H.264 압축, 모션 블러를 단계적으로 적용하여, VLM의 사고 시점·위치 판단 성능이 열화에 따라 어떻게 저하되는지 분석하는 평가 체계를 제시하였다. 원본 영상에서는 기존 보고 수준의 성능을 재현하였으며, [[(열화 결과: 어떤 판단이 어떤 열화에 가장 취약한지 1~2문장)]]. 이는 CCTV 기반 사고 탐지 시스템에서 관리해야 할 화질 조건을 판단 능력별로 제시한다는 점에서 의미가 있다. 다만 본 연구는 하나의 모델과 제한된 수의 영상을 사용하였고, 열화를 합성으로 재현하였다는 한계가 있다. 향후에는 다른 VLM과 더 많은 영상으로 분석을 확장하고, 열화에 강건한 학습 및 복원 기법과 합성 데이터를 활용한 학습 방향을 연구할 계획이다.')
p=para('참 고 문 헌',10,True,C,before=8,after=3)
refs=['마르와 차차 안드레아, 이충권, 김양석, 노미진, 문상일, 신재호, “YOLO v8을 활용한 컴퓨터 비전 기반 교통사고 탐지”, 한국산업정보학회논문지, 제29권, 제1호, pp. 91-105, 2024.',
'L. Picek, M. Čermák, M. Hanzl, V. Čermák, “ACCIDENT: A Benchmark Dataset for Vehicle Accident Detection from Traffic Surveillance Videos”, Proc. of IEEE/CVF Conf. on Computer Vision and Pattern Recognition Workshops (CVPRW), 2026.',
'M. O’Byrne, M. Sugrue, Vibhoothi, A. Kokaram, “Impact of Video Compression on the Performance of Object Detection Systems for Surveillance Applications”, Proc. of IEEE Int. Conf. on Advanced Video and Signal Based Surveillance (AVSS), 2022.',
'J. Cai, Y. Gao, J. Tang, “Robustness Benchmark Evaluation and Optimization for Real-Time Vehicle Detection under Multiple Adverse Conditions”, Applied Sciences, Vol. 15, No. 9, 4950, 2025.',
'윤영두, 김호, “영상 데이터 감쇄에 따른 보행자·차량 객체 탐지AI 신뢰도의 비선형적 성능 저하 메커니즘과 정량적 변곡점 규명: COCO 데이터 세트 기반 YOLOv8 사례연구”, 한국콘텐츠학회논문지, 제26권, 제8호, pp. 71-85, 2026.',
'M. Deitke et al., “Molmo and PixMo: Open Weights and Open Data for State-of-the-Art Vision-Language Models”, Proc. of IEEE/CVF Conf. on Computer Vision and Pattern Recognition (CVPR), pp. 91-104, 2025.',
'권오설, “원격 영상에서 심층 잔차 밀집 기반의 초고해상도 기법을 이용한 차량 검출 알고리즘”, 방송공학회논문지, 제28권, 제1호, pp. 124-131, 2023.',
'M. Poyser, A. Atapour-Abarghouei, T. P. Breckon, “On the Impact of Lossy Image and Video Compression on the Performance of Deep Convolutional Neural Network Architectures”, Proc. of 25th Int. Conf. on Pattern Recognition (ICPR 2020), pp. 2830-2837, 2021.']
for i,r in enumerate(refs,1):
    p=para(f'[{i}] {r}',9,align=WD_ALIGN_PARAGRAPH.JUSTIFY,ls=1.3,indent=False)
    p.paragraph_format.left_indent=Mm(5); p.paragraph_format.first_line_indent=Mm(-5)
d.save(OUT)
