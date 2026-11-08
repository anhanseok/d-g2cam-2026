const CFB=require('cfb');const fs=require('fs');
const [src,dir,out]=process.argv.slice(2);
const cfb=CFB.read(fs.readFileSync(src),{type:'buffer'});
const put=(p,file)=>{const d=fs.readFileSync(file);const e=CFB.find(cfb,p);if(e){e.content=d;e.size=d.length;}else CFB.utils.cfb_add(cfb,p,d);};
put('/DocInfo',dir+'DocInfo.bin');put('/BodyText/Section1',dir+'Section1.bin');
CFB.utils.cfb_del(cfb,'/BinData/BIN0002.bmp');CFB.utils.cfb_add(cfb,'/BinData/BIN0002.png',fs.readFileSync(dir+'BIN0002.png.bin'));
fs.writeFileSync(out,CFB.write(cfb,{type:'buffer',fileType:'cfb'}));
console.log(cfb.FullPaths.join('\n'));
