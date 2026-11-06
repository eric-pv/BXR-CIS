#!/usr/bin/env python3
"""Apply BXR CIS v3.2 theme colors/fonts and default master typography to a PPTX.
Usage: python apply-bxr-theme.py input.pptx output.pptx
Only input/output are modified as explicit paths; originals remain untouched.
"""
import argparse
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET
A="{http://schemas.openxmlformats.org/drawingml/2006/main}"
P="{http://schemas.openxmlformats.org/presentationml/2006/main}"
COLORS={"dk1":"0B0F14","lt1":"FFFFFF","dk2":"1E252D","lt2":"F2F4F6",
"accent1":"D02753","accent2":"173A55","accent3":"2E5C9A",
"accent4":"596B42","accent5":"6FC3D1","accent6":"5B6670","hlink":"2E5C9A","folHlink":"A51C40"}
def theme(data):
    root=ET.fromstring(data);scheme=root.find(".//"+A+"clrScheme")
    if scheme is None:return data
    scheme.set("name","BXR CIS v3.2")
    for node in scheme:
        name=node.tag.split("}")[-1]
        if name not in COLORS:continue
        node.clear();ET.SubElement(node,A+"srgbClr",{"val":COLORS[name]})
    for family in ("majorFont","minorFont"):
        element=root.find(".//"+A+family)
        if element is None:continue
        for script in ("latin","ea","cs"):
            font=element.find(A+script)
            if font is not None:font.set("typeface","Noto Sans TC")
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)
def master(data):
    root=ET.fromstring(data);styles=root.find(".//"+P+"txStyles")
    if styles is None:return data
    for section,size in (("titleStyle",2600),("bodyStyle",1800),("otherStyle",1400)):
        node=styles.find(P+section)
        if node is None:continue
        for i,level in enumerate(node):
            if not level.tag.split("}")[-1].startswith("lvl"):continue
            props=level.find(A+"defRPr")
            if props is None:props=ET.SubElement(level,A+"defRPr")
            props.set("sz",str(max(1000,size-i*200)))
            for script in ("latin","ea","cs"):
                font=props.find(A+script)
                if font is not None:font.set("typeface","Noto Sans TC")
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)
def convert(src,dst):
    if Path(src).resolve()==Path(dst).resolve():raise ValueError("Input and output must be different")
    with ZipFile(src) as z,ZipFile(dst,"w",ZIP_DEFLATED) as out:
        for entry in z.infolist():
            data=z.read(entry.filename);n=entry.filename
            if n.startswith("ppt/theme/") and n.endswith(".xml"):data=theme(data)
            if n.startswith("ppt/slideMasters/slideMaster") and n.endswith(".xml"):data=master(data)
            out.writestr(entry,data)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("input");p.add_argument("output")
    args=p.parse_args();convert(args.input,args.output)
