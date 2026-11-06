#!/usr/bin/env node
/** Minimal editable three-layout technology pilot, with backgrounds/logo on slide layouts.
 * Prerequisite: npm install pptxgenjs
 * Usage: node build-military-pilot.js <repo-root> <official-logo-png> <output.pptx>
 * This demonstrates layout/master inheritance, NOT a finished production generator.
 */
const fs=require("fs"),path=require("path"),pptxgen=require("pptxgenjs");
const [root,logo,out]=process.argv.slice(2);
if(!root||!logo||!out)throw Error("Usage: node build-military-pilot.js <repo-root> <official-logo-png> <output.pptx>");
const p=new pptxgen();p.layout="LAYOUT_WIDE";p.author="Big x Reality";p.lang="zh-TW";
p.theme={headFontFace:"Noto Sans TC",bodyFontFace:"Noto Sans TC",lang:"zh-TW"};
const W=13.333333,H=7.5,assets=path.join(root,"presentation-skill","approved-layouts","military-tech");
function define(name,file,dark){
  const img=path.join(assets,file);
  if(!fs.existsSync(img))throw Error("Missing approved background: "+img);
  const objects=[{image:{path:img,x:0,y:0,w:W,h:H}}];
  if(!fs.existsSync(logo))throw Error("Missing official logo: "+logo);
  objects.push({image:{path:logo,x:12.4,y:6.65,w:.48,h:.48}});
  p.defineSlideMaster({title:name,background:{color:dark?"0B0F14":"FFFFFF"},objects});
}
define("COVER","BXR_Military_Cover_16x9.png",true);
define("SECTION","BXR_Military_Section_16x9.png",true);
define("CONTENT","BXR_Military_Content_White_16x9.png",false);
function txt(s,value,x,y,w,h,sz,color="FFFFFF",bold=false){s.addText(value,{x,y,w,h,fontFace:"Noto Sans TC",fontSize:sz,color,bold,margin:0,fit:"shrink"});}
let s=p.addSlide("COVER");
txt(s,"簡報標題（可編輯）",5,2.5,7.5,.9,36,"FFFFFF",true);
txt(s,"副標題／日期（可編輯）",5,3.5,7.5,.5,18,"C5CCD3");
s=p.addSlide("SECTION");
txt(s,"01",7.15,2.3,3,1,48,"6FC3D1",true);
txt(s,"章節名稱（可編輯）",7.15,3.4,5.4,.9,34,"FFFFFF",true);
s=p.addSlide("CONTENT");
txt(s,"內容頁標題（可編輯）",.75,1.25,11.5,.7,26,"0B0F14",true);
txt(s,"此處填入產品介紹、圖表、流程或比較表。",.75,2.25,11.6,.8,19,"1E252D");
p.writeFile({fileName:out});
