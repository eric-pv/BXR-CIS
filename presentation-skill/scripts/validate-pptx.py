#!/usr/bin/env python3
"""Read-only OOXML structure check; PowerPoint visual QA still mandatory."""
import argparse,json,re,zipfile,xml.etree.ElementTree as ET
NS={"p":"http://schemas.openxmlformats.org/presentationml/2006/main","a":"http://schemas.openxmlformats.org/drawingml/2006/main"}
SLIDE=re.compile(r"ppt/slides/slide\d+\.xml$")
MASTER=re.compile(r"ppt/slideMasters/slideMaster\d+\.xml$")
LAYOUT=re.compile(r"ppt/slideLayouts/slideLayout\d+\.xml$")
def validate(file):
    with zipfile.ZipFile(file) as z:
        members=z.namelist()
        slides=sorted(s for s in members if SLIDE.fullmatch(s))
        masters=[s for s in members if MASTER.fullmatch(s)]
        layouts=[s for s in members if LAYOUT.fullmatch(s)]
        rows=[]
        for name in slides:
            xml=ET.fromstring(z.read(name))
            rows.append({"slide":name,"native_text_runs":len(xml.findall(".//a:t",NS)),
                         "native_shapes":len(xml.findall(".//p:sp",NS)),
                         "pictures":len(xml.findall(".//p:pic",NS)),
                         "timing_xml":int(xml.find(".//p:timing",NS) is not None)})
        warnings=[]
        if not masters:warnings.append("No slide master")
        if any(row["native_text_runs"]==0 for row in rows):warnings.append("Some slides have no native editable text")
        warnings.append("Still requires PowerPoint open/repair/visual/overflow/logo/animation QA")
        return {"slides":len(slides),"masters":len(masters),"layouts":len(layouts),"details":rows,"warnings":warnings}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("pptx");args=p.parse_args()
    print(json.dumps(validate(args.pptx),ensure_ascii=False,indent=2))
