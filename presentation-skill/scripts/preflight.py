#!/usr/bin/env python3
"""BXR preparation preflight. Checks concrete asset paths, fixture shape and the approved background hashes.
No slide-design judgments. Standard library only.
"""
import argparse,csv,hashlib,json,re,sys
from pathlib import Path
REQUIRED_BRIEF=("id","topic","language","audience","purpose","slides","content")
LANGUAGES={"zh-TW","en","jp"}
EXPECTED_BACKGROUNDS={"BXR_Military_Cover_16x9.png","BXR_Military_Section_16x9.png","BXR_Military_Content_White_16x9.png"}
def issue(errors,message):errors.append(message)
def check(root,require_lfs=False):
    base=root/"presentation-skill"
    errors=[];warnings=[];results={}
    for name in ("00_Brand_Guidelines/v3.2","01_Logo","02_Color/BXR_Colors_v3.2.json","03_Fonts","04_Graphics/Icons","07_Templates/BXR_Presentation_Template_v3.2.pptx"):
        if not (root/name).exists():issue(errors,"missing authoritative source "+name)
    for name in ("contracts/presentation-brief.schema.json","contracts/deck-plan.schema.json","config/presentation-theme.json"):
        path=base/name
        try:
            o=json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(o,dict):issue(errors,"not a JSON object: "+name)
        except Exception as exc:issue(errors,"invalid JSON "+name+": "+str(exc))
    approved=base/"approved-layouts/military-tech"
    observed={p.name for p in approved.glob("*.png")}
    if observed!=EXPECTED_BACKGROUNDS:issue(errors,"approved PNG set mismatch missing="+str(sorted(EXPECTED_BACKGROUNDS-observed))+" extra="+str(sorted(observed-EXPECTED_BACKGROUNDS)))
    sha_file=approved/"assets.sha256"
    if sha_file.exists():
        for row in sha_file.read_text(encoding="utf-8").splitlines():
            match=re.match(r"^([a-fA-F0-9]{64})\s+(.+)$",row)
            if not match:issue(errors,"malformed sha256 line: "+row);continue
            expected,name=match.groups()
            path=approved/name
            if not path.exists():issue(errors,"hash target missing "+name);continue
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            if actual!=expected.lower():issue(errors,"hash mismatch "+name)
    else:issue(errors,"missing assets.sha256")
    fixtures=sorted((base/"tests/fixtures/briefs").glob("*.json"))
    if not fixtures:issue(errors,"no test briefs")
    for path in fixtures:
        try:
            v=json.loads(path.read_text(encoding="utf-8"))
            for field in REQUIRED_BRIEF:
                if field not in v:issue(errors,path.name+": missing "+field)
            if v.get("language") not in LANGUAGES:issue(errors,path.name+": bad language")
            if not isinstance(v.get("slides"),int) or isinstance(v.get("slides"),bool) or not 3<=v["slides"]<=60:issue(errors,path.name+": invalid slide count")
            if not isinstance(v.get("content"),list) or not v["content"]:issue(errors,path.name+": no content")
        except Exception as exc:issue(errors,"bad fixture "+path.name+": "+str(exc))
    icon_file=base/"catalog/icon-catalog.csv"
    if icon_file.exists():
        with icon_file.open(encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        for row in rows:
            if "path" in row and not (root/"04_Graphics/Icons"/row["path"]).exists():
                issue(errors,"icon catalog unresolved: "+row["path"])
        results["cataloged_icons"]=len(rows)
    else:issue(errors,"missing icon catalog")
    for name in ("500頁.pptx","Aviation Slides.zip"):
        path=base/"source-library"/name
        if not path.exists():issue(errors,"missing source archive "+name)
        elif path.stat().st_size<1000000:
            (errors if require_lfs else warnings).append(name+": likely LFS pointer; run git lfs pull")
    results.update({"fixtures":len(fixtures),"approved_backgrounds":len(observed),"errors":errors,"warnings":warnings,"status":"PASS" if not errors else "FAIL"})
    return results
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",default=".");p.add_argument("--require-lfs",action="store_true");a=p.parse_args()
    result=check(Path(a.repo).resolve(),a.require_lfs)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if not result["errors"] else 1
if __name__=="__main__":sys.exit(main())
