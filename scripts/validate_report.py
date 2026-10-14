"""Validate PBIR against Microsoft's schemas, with local caching for offline CI."""
import argparse
import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urljoin
from jsonschema import Draft7Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/"schemas"
HOST = "https://developer.microsoft.com/json-schemas/"


def retrieve(uri):
    if not uri.startswith(HOST):
        raise ValueError(f"Unexpected schema URL: {uri}")
    path = CACHE/uri.removeprefix(HOST)
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        with urllib.request.urlopen(uri,timeout=40) as f:
            path.write_bytes(f.read())
    return Resource.from_contents(json.loads(path.read_text()))


def validate(root):
    registry=Registry(retrieve=retrieve)
    count=0
    for path in sorted(p for p in root.rglob("*") if p.suffix in (".json",".pbip",".pbir",".pbism")):
        data=json.loads(path.read_text())
        if "$schema" not in data: continue
        uri=data["$schema"]
        schema=retrieve(uri).contents
        validator=Draft7Validator(schema,registry=registry)
        errors=list(validator.iter_errors(data))
        if errors:
            for e in errors: print(path.relative_to(ROOT),list(e.path),e.message)
            raise SystemExit("Invalid PBIR")
        count+=1
    print(f"Microsoft JSON schemas: {count} definitions passed")


if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=ROOT/"powerbi")
    validate(p.parse_args().root)
