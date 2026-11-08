import sys,struct as S,zlib
sys.path.insert(0,'/tmp/claude-0')
from hwplib import recs,enc,comp
import olefile
f=olefile.OleFileIO('/tmp/claude-0/v5/in.hwp')
R=[list(x) for x in recs(zlib.decompress(f.openstream('BodyText/Section1').read(),-15))]
D=[list(x) for x in recs(zlib.decompress(f.openstream('DocInfo').read(),-15))]
# 1) table captions (para shape 8): keep with next paragraph (the table)
psi=[i for i,(t,l,p) in enumerate(D) if t==25][8]
p=bytearray(D[psi][2]); a=S.unpack('<I',p[:4])[0]|(1<<17); p[:4]=S.pack('<I',a); D[psi][2]=bytes(p)
# 2) drop the runs of blank paragraphs used as manual spacing (keep one blank)
def para_span(i):
    j=i+1
    while j<len(R) and R[j][1]>R[i][1]: j+=1
    return j
drop=set()
heads=[i for i,(t,l,p) in enumerate(R) if t==66 and l==0]
def isblank(i): return (S.unpack('<I',R[i][2][:4])[0]&0x7fffffff)==1
run=[]
for i in heads+[None]:
    if i is not None and isblank(i): run.append(i); continue
    if len(run)>=3:
        for k in run[1:]: drop.update(range(k,para_span(k)))
    run=[]
R=[x for i,x in enumerate(R) if i not in drop]
print('dropped paragraphs:',sum(1 for i in drop if i in heads))
# 3) strip top-level linesegs so 한글 re-lays out (keep picture paragraph)
heads=[i for i,(t,l,p) in enumerate(R) if t==66 and l==0]
for i in heads[1:]:
    j=para_span(i)
    if any(R[k][0]==71 and R[k][2][:4]==b' osg' for k in range(i,j)): continue
    h=bytearray(R[i][2]); h[16:18]=S.pack('<H',0); R[i][2]=bytes(h)
    for k in range(i+1,j):
        if R[k][0]==69 and R[k][1]==1: R[k][0]=None
R=[x for x in R if x[0] is not None]
open('/tmp/claude-0/v5/out/Section1.bin','wb').write(comp(enc(R)))
open('/tmp/claude-0/v5/out/DocInfo.bin','wb').write(comp(enc(D)))
