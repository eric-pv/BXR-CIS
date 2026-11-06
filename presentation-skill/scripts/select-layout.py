#!/usr/bin/env python3
"""Suggest CIS-approved candidate layouts only. Unreviewed paid templates are NEVER auto-selected."""
import argparse,csv,json
ROLES={
"comparison":["comparison","versus","比較","對照","優缺點"],
"timeline":["timeline","milestone","roadmap","時程","年表","時間軸"],
"process":["process","steps","workflow","流程","步驟"],
"map":["map","地圖","國家","全球分布"],
"data":["chart","statistics","數據","趨勢","圖表","kpi"],
"team":["team","people","人員","團隊","成員"],
"product":["product","feature","產品","功能","設備"],
"section":["chapter","section","章節","過渡"],
"agenda":["agenda","目錄","大綱"]}
def role(brief):
    txt=brief.casefold()
    scores=[(sum(len(word) if word in txt else 0 for word in words),-i,name) for i,(name,words) in enumerate(ROLES.items())]
    score,_,name=max(scores)
    return name if score else "general"
def choose(catalog,brief):
    wanted=role(brief);candidates=[]
    with open(catalog,encoding="utf-8-sig",newline="") as f:
        for item in csv.DictReader(f):
            approved=item.get("approval")=="approved" or item.get("cis_approved") in ("yes","true")
            if not approved or item.get("category_auto")!=wanted:continue
            shapes=int(item.get("shapes",0) or 0);images=int(item.get("images",item.get("pictures",0)) or 0)
            score=10+min(shapes,16)*.2+min(images,5)*.1
            candidates.append({"id":item.get("layout_id",item.get("id")),"score":round(score,2),"source":item.get("source_file",item.get("source"))})
    candidates.sort(key=lambda x:-x["score"])
    return {"role":wanted,"candidate_layouts":candidates[:5],
            "fallback":"Use official BXR template or one of three approved military backgrounds and create native editable shapes" if not candidates else None}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("catalog");p.add_argument("brief");args=p.parse_args()
    print(json.dumps(choose(args.catalog,args.brief),ensure_ascii=False,indent=2))
