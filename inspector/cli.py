import sys, json, os
from . import __version__
from .parser import registry
from .parsers import png
from .graph import generate as graph_generate, build_from_artifact
from .memory import database as mem_db

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

def cmd_index(args):
    """Scan and index a directory of images into Artifact Memory."""
    root = args.directory
    if not os.path.isdir(root):
        print(f"Error: directory not found: {root}", file=sys.stderr)
        sys.exit(1)
    mem_db.init()
    count = 0
    total = sum(1 for _, _, fs in os.walk(root) for f in fs if f.lower().endswith('.png'))
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.lower().endswith('.png'):
                continue
            fp = os.path.join(dirpath, f)
            try:
                result = registry.parse(fp)
                if result and result.source_tool:
                    aid = mem_db.save(result, fp)
                    if aid:
                        count += 1
            except Exception:
                pass
            if count % 10 == 0 and count > 0:
                print(f"  Indexed: {count}/{total}", flush=True)
    stats = mem_db.get_stats()
    print(f"  Done: {count} files indexed")
    print(f"  Sources: {stats['sources']}, Models: {stats['models']}")

def cmd_mcp(args):
    from .mcp.server import main as mcp_main
    mcp_main()

def cmd_explore(args):
    """Launch the Artifact Explorer web UI."""
    from .explorer.server import main as explorer_main
    explorer_main(port=args.port)

def cmd_benchmark(args):
    """Run parser benchmark against a directory of images."""
    import glob, time
    root = args.directory
    if not os.path.isdir(root):
        print(f"Error: directory not found: {root}", file=sys.stderr)
        sys.exit(1)
    pngs = sorted(glob.glob(root + '/**/*.png', recursive=True))
    if not pngs:
        print("No PNG files found.")
        return
    total = len(pngs)
    ok = {'comfyui': 0, 'model': 0, 'prompt': 0, 'seed': 0, 'sampler': 0}
    for fp in pngs:
        try:
            r = registry.parse(fp)
            if r and r.source_tool:
                ok['comfyui'] += 1
                if r.generation:
                    if r.generation.model: ok['model'] += 1
                    if r.generation.prompt: ok['prompt'] += 1
                    if r.generation.seed > 0: ok['seed'] += 1
                    if r.generation.sampler: ok['sampler'] += 1
        except:
            pass
    print(f"\nParser Benchmark: {total} images")
    print(f"{'='*40}")
    for k in ['comfyui', 'model', 'prompt', 'seed', 'sampler']:
        pct = int(ok[k] / total * 100)
        bar = '#' * (pct // 5) + '-' * (20 - pct // 5)
        print(f"  {k:10s} {ok[k]:4d}/{total} ({pct:2d}%) |{bar}|")
    print(f"\nReport: {total} files, {ok['comfyui']} detected, {(total-ok['comfyui'])} failed")
    return ok

def cmd_graph(args):
    mem_db.init()
    mem_db.build_relations()
    stats = mem_db.get_stats()
    print(f"Artifact Memory Graph")
    print(f"  {stats['total']} assets, {stats['sources']} sources, {stats['models']} models")
    print()
    results = mem_db.list_all(30)
    for r in results:
        rels = mem_db.get_related(r["id"], 3)
        rel_str = ", ".join([f"{rel['relation']} → {rel['file'][:20]}" for rel in rels]) if rels else "(no relations)"
        print(f"  [{r['id']}] {r['file']:25s} | {r['source']:10s} | {rel_str}")

def cmd_related(args):
    mem_db.init()
    aid = args.artifact_id
    results = mem_db.get_related(aid)
    if not results:
        print(f"No relations found for artifact #{aid}.")
        return
    print(f"Relations for artifact #{aid}:")
    for r in results:
        print(f"  [{r['id']}] {r['file']:25s} | {r['relation']:15s} | {r['confidence']:.1f} | {r['model'][:25]} | {r['source']}")

def cmd_history(args):
    mem_db.init()
    aid = args.artifact_id
    data = mem_db.get_history(aid)
    if not data:
        print(f"Artifact #{aid} not found.")
        return
    a = data["artifact"]
    print(f"Artifact #{aid}: {a['file']}")
    print(f"  Source:   {a['source']}")
    print(f"  Model:    {a['model']}")
    print(f"  Prompt:   {a['prompt'][:60]}")
    print(f"  Seed:     {a['seed']}")
    print(f"  Steps:    {a['steps']} | CFG: {a['cfg']} | Sampler: {a['sampler']}")
    print(f"  Scanned:  {a['scanned']}")
    if data["nodes"]:
        print(f"\n  Workflow Nodes:")
        for n in data["nodes"]:
            print(f"    → {n['type']}")
    if data["related"]:
        print(f"\n  Related Assets:")
        for r in data["related"]:
            print(f"    [{r['id']}] {r['file']:25s} | {r['relation']:15s} | {r['model'][:25]}")

def cmd_mem_search(args):
    """Search indexed artifacts."""
    mem_db.init()
    results = mem_db.search(args.query, limit=args.limit)
    if not results:
        print("No matching artifacts found.")
        return
    print(f"Found {len(results)} artifacts:")
    for r in results:
        print(f"  [{r['id']}] {r['file']} | {r['source']} | {r['model']} | {r['prompt'][:50]}")

def cmd_mem_list(args):
    """List all indexed artifacts."""
    mem_db.init()
    stats = mem_db.get_stats()
    print(f"Artifact Memory: {stats['total']} assets, {stats['sources']} sources, {stats['models']} models")
    print()
    results = mem_db.list_all(limit=args.limit)
    for r in results:
        print(f"  [{r['id']}] {r['file']:30s} {r['source']:10s} {r['model'][:25]:25s} {r['scanned']}")

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
    sub.add_parser("mcp", help="Start MCP server for AI Agent access")
    p_exp = sub.add_parser("explore", help="Launch Artifact Explorer web UI")
    p_exp.add_argument("--port", type=int, default=8765, help="Web server port")
    p_bench = sub.add_parser("benchmark", help="Run parser benchmark against a directory of images")
    p_bench.add_argument("directory", help="Directory of AI-generated PNG images")
    p_idx = sub.add_parser("index", help="Index images into Artifact Memory")
    p_idx.add_argument("directory", help="Directory of AI-generated images")
    p_s = sub.add_parser("search", help="Search indexed artifacts")
    p_s.add_argument("query", help="Search query")
    p_s.add_argument("--limit", type=int, default=20)
    p_l = sub.add_parser("list", help="List all indexed artifacts")
    p_l.add_argument("--limit", type=int, default=100)
    sub.add_parser("graph", help="Show artifact relationship graph")
    p_rel = sub.add_parser("related", help="Find related artifacts")
    p_rel.add_argument("artifact_id", type=int, help="Artifact ID")
    p_h = sub.add_parser("history", help="Show creation history of an artifact")
    p_h.add_argument("artifact_id", type=int, help="Artifact ID")
    args = parser.parse_args()
    if args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "parsers":
        cmd_parsers(args)
    elif args.command == "index":
        cmd_index(args)
    elif args.command == "search":
        cmd_mem_search(args)
    elif args.command == "list":
        cmd_mem_list(args)
    elif args.command == "mcp":
        cmd_mcp(args)
    elif args.command == "explore":
        cmd_explore(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "graph":
        cmd_graph(args)
    elif args.command == "related":
        cmd_related(args)
    elif args.command == "history":
        cmd_history(args)

if __name__ == "__main__":
    main()