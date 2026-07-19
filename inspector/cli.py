import sys, json, os
from . import __version__
from .parser import registry
from .parsers import png
from .graph import generate as graph_generate, build_from_artifact

def cmd_inspect(args):
    path = args.path
    if not os.path.exists(path):
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    result = registry.parse(path)
    if result is None:
        print(f"Error: no parser available for: {path}", file=sys.stderr)
        sys.exit(1)
    data = result.to_dict()
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    if args.graph:
        info = build_from_artifact(result)
        svg = graph_generate(result.workflow_json or "{}")
        print(svg)
        return
    if args.schema:
        info = build_from_artifact(result)
        print(json.dumps(info.to_dict(), indent=2, ensure_ascii=False))
        return
    _print_report(data)

def _print_report(data):
    gen = data.get("generation") or {}
    print(f"File:     {data['path']}")
    print(f"Type:     {data['file_type']}")
    print(f"Source:   {data.get('source_tool') or 'Unknown'}")
    print(f"Parser:   {data['parser_name']}")
    sz = data.get('file_size', 0)
    print(f"Size:     {sz:,} bytes")
    print("")
    print("Generation:")
    print(f"  Model:   {gen.get('model', 'N/A')}")
    prompt = gen.get('prompt', '')
    print(f"  Prompt:  {prompt[:80] if prompt else 'N/A'}")
    neg = gen.get('negative_prompt', '')
    if neg:
        print(f"  Neg:     {neg[:60]}")
    seed = gen.get('seed', -1)
    print(f"  Seed:    {seed if seed >= 0 else 'N/A'}")
    for lora in gen.get("loras", []):
        print(f"  LoRA:    {lora['name']} ({lora['weight']})")
    steps = gen.get('steps', 0)
    if steps:
        print(f"  Steps:   {steps}")
    cfg = gen.get('cfg', 0.0)
    if cfg:
        print(f"  CFG:     {cfg}")
    samp = gen.get('sampler', '')
    if samp:
        print(f"  Sampler: {samp}")

def cmd_scan(args):
    root = args.directory
    if not os.path.isdir(root):
        print(f"Error: directory not found: {root}", file=sys.stderr)
        sys.exit(1)
    exts = {'.png'}
    files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if os.path.splitext(f)[1].lower() in exts:
                files.append(os.path.join(dirpath, f))
    if not files:
        print("No supported files found.")
        return
    total = len(files)
    results = []
    types = {}
    errors = 0
    for i, fp in enumerate(files):
        rel = os.path.relpath(fp, root)
        sys.stdout.write(f"\r  Scanning: {i+1}/{total}")
        sys.stdout.flush()
        result = registry.parse(fp)
        if result:
            source = result.source_tool or "Unknown"
            types[source] = types.get(source, 0) + 1
            if args.json:
                results.append(result.to_dict())
        else:
            errors += 1
    print()
    print()
    print(f"  Scanned: {total} files")
    print(f"  Errors:  {errors}")
    print()
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")
    if args.json:
        out_path = args.output or "artifact_report.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"total": total, "errors": errors, "types": types, "results": results}, f, indent=2, ensure_ascii=False)
        print(f"\n  Report: {out_path}")

def cmd_parsers(_args):
    parsers = registry.list_parsers()
    if not parsers:
        print("No parsers registered.")
        return
    print(f"Registered parsers ({len(parsers)}):")
    for p in parsers:
        print(f"  - {p['name']}")

def main():
    import argparse
    parser = argparse.ArgumentParser(prog="artifact", description="AI Artifact Inspector")
    parser.add_argument("--version", action="version", version=f"artifact {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect", help="Inspect an AI-generated file")
    p.add_argument("path", help="Path to the file")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--graph", action="store_true", help="Output workflow as SVG diagram")
    p.add_argument("--schema", action="store_true", help="Output Universal Artifact Schema as JSON")
    s = sub.add_parser("scan", help="Batch scan a directory of files")
    s.add_argument("directory", help="Directory to scan")
    s.add_argument("--json", action="store_true", help="Export results as JSON")
    s.add_argument("-o", "--output", default=None, help="Output path for JSON report")
    sub.add_parser("parsers", help="List registered parsers")
    args = parser.parse_args()
    if args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "parsers":
        cmd_parsers(args)

if __name__ == "__main__":
    main()