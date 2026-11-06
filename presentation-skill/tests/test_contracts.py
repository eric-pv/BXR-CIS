#!/usr/bin/env python3
"""Validate presentation data contracts and fixtures. Requires: pip install jsonschema."""
import json,sys
from pathlib import Path
from jsonschema import Draft202012Validator
def main():
    base=Path(__file__).resolve().parents[1]
    spec=base/"contracts"
    cases=[
        (spec/"presentation-brief.schema.json",list((base/"tests/fixtures/briefs").glob("*.json"))),
        (spec/"deck-plan.schema.json",[base/"tests/fixtures/expected-plan-police.json"]),
    ]
    total=0;failures=[]
    for schema_path,files in cases:
        schema=json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        checker=Draft202012Validator(schema)
        if not files:failures.append("no fixtures for "+schema_path.name)
        for path in files:
            data=json.loads(path.read_text(encoding="utf-8"))
            errors=list(checker.iter_errors(data))
            for err in errors:failures.append(f"{path.name} at {list(err.absolute_path)}: {err.message}")
            total+=1
    # Contract negative test: malformed brief MUST be rejected
    brief_schema=json.loads((spec/"presentation-brief.schema.json").read_text(encoding="utf-8"))
    sample=json.loads((base/"tests/fixtures/briefs/police-xr-overview.json").read_text(encoding="utf-8"))
    sample["slides"]=0
    if Draft202012Validator(brief_schema).is_valid(sample):failures.append("negative test accepted zero slides")
    print(f"validated {total} positive fixtures, 1 negative case; failures={len(failures)}")
    for err in failures:print("FAIL:",err)
    return 1 if failures else 0
if __name__=="__main__":sys.exit(main())
