#!/usr/bin/env python3
"""Index native PPTX slide XML in 500頁.pptx and nested Aviation Slides.zip without extraction."""
import argparse,csv,hashlib,html,io,re,zipfile
from pathlib import Path
SLIDE=re.compile(r"^ppt/slides/slide(\d+)\.xml$")
TEXT=re.compile(rb"<a:t(?:\s[^>]*)?>(.*?)</a:t>",re.S)
FIELDS=["layout_id","library","source","slide_number","category_auto","shapes","images","groups","text_runs","timing_xml","sample_text","approval"]
TAGS={"timeline":["timeline","milestone","roadmap","时间轴"],"map":["map","地图"],"comparison":["comparison","versus"],"process":["process","steps","流程"],"data":["chart","statistics","kpi"],"product":["product","产品"],"agenda":["agenda","目录"],"section":["section","过渡"]}
def inspect(source,library,label,prefix):
    with zipfile.ZipFile(source) as z:
        for member in z.infolist():
            m=SLIDE.fullmatch(member.filename)
            if not m: continue
            if member.file_size>10_000_000:
                n=int(m.group(1))
                yield [f"{prefix}-{n:04d}",library,label,n,"oversize-unparsed",0,0,0,0,0,"Slide XML exceeds safe parse limit","pending"]
                continue
            xml=z.read(member)
            txt=" ".join(html.unescape(s.decode("utf-8","replace")) for s in TEXT.findall(xml)[:60])[:180]
            hay=(label+" "+txt).casefold()
            cat=next((k for k,keys in TAGS.items() if any(key in hay for key in keys)),"general")
            n=int(m.group(1))
            yield [f"{prefix}-{n:04d}",library,label,n,cat,xml.count(b"<p:sp>"),xml.count(b"<p:pic>"),max(xml.count(b"<p:grpSp>")-1,0),len(TEXT.findall(xml)),int(b"<p:timing" in xml),txt,"pending"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--big-deck",required=True);p.add_argument("--aviation-zip",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    count=0;decks=[]
    with (out/"layouts.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f);w.writerow(FIELDS)
        with open(a.big_deck,"rb") as fp:
            for row in inspect(fp,"500pages","500頁.pptx","PMLD"):w.writerow(row);count+=1
        with zipfile.ZipFile(a.aviation_zip) as archive:
            entries=sorted((x for x in archive.infolist() if x.filename.lower().endswith(".pptx") and not x.filename.split("/")[-1].startswith("._") and "__MACOSX" not in x.filename),key=lambda x:x.filename)
            for i,item in enumerate(entries,1):
                raw=archive.read(item);n=0
                try:
                    for row in inspect(io.BytesIO(raw),"aviation",item.filename,f"AVI-{i:03d}"):w.writerow(row);count+=1;n+=1
                except (zipfile.BadZipFile,ValueError):pass
                decks.append([f"AVI-{i:03d}",item.filename,n,item.file_size,hashlib.sha256(raw).hexdigest()])
    with (out/"aviation-decks.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f);w.writerow(["deck_id","zip_entry","slide_count","size_bytes","sha256"]);w.writerows(decks)
    print("indexed slide XML:",count,"aviation PPTX decks:",len(decks))
    print("Note: heuristic categories only; none CIS approved. Timing XML is not animation proof.")
if __name__=="__main__":main()
