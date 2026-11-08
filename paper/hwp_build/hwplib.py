import olefile,zlib,struct
TAGS={16:'DOCUMENT_PROPERTIES',17:'ID_MAPPINGS',18:'BIN_DATA',19:'FACE_NAME',20:'BORDER_FILL',21:'CHAR_SHAPE',22:'TAB_DEF',23:'NUMBERING',24:'BULLET',25:'PARA_SHAPE',26:'STYLE',66:'PARA_HEADER',67:'PARA_TEXT',68:'PARA_CHAR_SHAPE',69:'PARA_LINE_SEG',70:'PARA_RANGE_TAG',71:'CTRL_HEADER',72:'LIST_HEADER',73:'PAGE_DEF',74:'FOOTNOTE_SHAPE',75:'PAGE_BORDER_FILL',76:'SHAPE_COMPONENT',77:'TABLE',78:'SC_LINE',79:'SC_RECT',80:'SC_ELLIPSE',81:'SC_ARC',82:'SC_POLYGON',83:'SC_CURVE',84:'SC_OLE',85:'SC_PICTURE',86:'SC_CONTAINER',87:'CTRL_DATA',88:'EQEDIT',90:'SC_TEXTART'}
def recs(data):
    i=0;out=[]
    while i<len(data):
        h=struct.unpack('<I',data[i:i+4])[0];i+=4
        tag=h&0x3ff;lvl=(h>>10)&0x3ff;sz=h>>20
        if sz==0xfff: sz=struct.unpack('<I',data[i:i+4])[0];i+=4
        out.append([tag,lvl,data[i:i+sz]]);i+=sz
    return out
def enc(rs):
    b=bytearray()
    for tag,lvl,p in rs:
        sz=len(p)
        if sz>=0xfff: b+=struct.pack('<II',tag|(lvl<<10)|(0xfff<<20),sz)
        else: b+=struct.pack('<I',tag|(lvl<<10)|(sz<<20))
        b+=p
    return bytes(b)
def comp(b):
    c=zlib.compressobj(9,zlib.DEFLATED,-15);return c.compress(b)+c.flush()
