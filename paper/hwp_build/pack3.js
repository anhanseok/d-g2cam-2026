const CFB=require('cfb');const fs=require('fs');
const [src,sec,out]=process.argv.slice(2);
const cfb=CFB.read(fs.readFileSync(src),{type:'buffer'});
const d=fs.readFileSync(sec);const e=CFB.find(cfb,'/BodyText/Section1');e.content=d;e.size=d.length;
fs.writeFileSync(out,CFB.write(cfb,{type:'buffer',fileType:'cfb'}));
