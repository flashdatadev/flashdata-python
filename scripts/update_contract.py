"""Refresh the SDK's API-key OpenAPI snapshot from a FlashData OpenAPI file."""

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def snapshot(source, previous):
    result = copy.deepcopy(previous)
    for path, methods in result["paths"].items():
        for method in methods:
            operation = copy.deepcopy(source["paths"][path][method])
            security = operation.get("security", [])
            operation["security"] = [item for item in security if set(item) == {"dataApiKey"}]
            if security and not operation["security"]:
                raise ValueError(f"{method} {path} no longer supports API keys")
            methods[method] = operation
    result["components"] = {"securitySchemes": {"dataApiKey": source["components"]["securitySchemes"]["dataApiKey"]}}

    def include_refs(value):
        if isinstance(value, list):
            for child in value:
                include_refs(child)
        elif isinstance(value, dict):
            ref = value.get("$ref", "")
            if ref.startswith("#/components/"):
                category, name = ref.removeprefix("#/components/").split("/")
                bucket = result["components"].setdefault(category, {})
                if name not in bucket:
                    bucket[name] = copy.deepcopy(source["components"][category][name])
                    include_refs(bucket[name])
            for child in value.values():
                include_refs(child)

    include_refs(result["paths"])
    # Keep existing component order so contract updates produce readable diffs.
    components = result["components"]
    result["components"] = {}
    for category in dict.fromkeys([*previous["components"], *components]):
        if category not in components:
            continue
        names = dict.fromkeys([*previous["components"].get(category, {}), *components[category]])
        result["components"][category] = {
            name: components[category][name] for name in names if name in components[category]
        }
    result["info"]["description"] = (
        "API-key authenticated data, jobs, bulk collections and account reads, plus public discovery. "
        "Includes JSON, plain-text and Markdown response options."
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, required=True, help="FlashData public OpenAPI JSON file")
    parser.add_argument("--check", action="store_true", help="Check the snapshot without writing")
    args = parser.parse_args()
    path = ROOT / "openapi.json"
    current = json.loads(path.read_text(encoding="utf-8"))
    updated = snapshot(json.loads(args.openapi.read_text(encoding="utf-8")), current)
    if args.check:
        if current != updated:
            parser.exit(1, "OpenAPI snapshot is out of date. Run without --check to refresh it.\n")
        print("OpenAPI snapshot matches the supplied contract.")
    else:
        path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Updated OpenAPI snapshot.")


if __name__ == "__main__":
    main()
