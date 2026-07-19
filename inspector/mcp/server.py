"""Minimal MCP server for AI Artifact Memory.

Exposes the artifact database as 5 tools that any MCP-compatible
Agent (Claude, Cursor, Continue) can call.

Usage:
    artifact mcp                 # Start MCP server on stdio
"""
import sys, json, os
from ..memory import database as mem_db


def handle_call(tool_name, args):
    if tool_name == "search_artifacts":
        q = args.get("query", "")
        results = mem_db.search(q)
        return {"count": len(results), "assets": results}

    elif tool_name == "get_artifact":
        aid = args.get("artifact_id", 0)
        data = mem_db.get_by_id(aid)
        if not data:
            return {"error": "Artifact not found"}
        return {"artifact": data}

    elif tool_name == "get_workflow":
        aid = args.get("artifact_id", 0)
        data = mem_db.get_by_id(aid)
        if not data:
            return {"error": "Artifact not found"}
        from ..graph import generate
        svg = generate(data.get("workflow_json", ""))
        return {"svg": svg}

    elif tool_name == "similar_assets":
        return {"note": "Semantic search coming in v0.4. Currently returns text matches.", "assets": []}

    elif tool_name == "collection_stats":
        return mem_db.get_stats()

    return {"error": f"Unknown tool: {tool_name}"}


def main():
    tools = [
        {"name": "search_artifacts", "description": "Search AI-generated assets by text (model name, prompt, source)", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search term"}}, "required": ["query"]}},
        {"name": "get_artifact", "description": "Get full generation details for a specific artifact by ID", "parameters": {"type": "object", "properties": {"artifact_id": {"type": "integer", "description": "Artifact ID from search results"}}, "required": ["artifact_id"]}},
        {"name": "get_workflow", "description": "Get the workflow visualization graph for an artifact as SVG", "parameters": {"type": "object", "properties": {"artifact_id": {"type": "integer", "description": "Artifact ID"}}, "required": ["artifact_id"]}},
        {"name": "similar_assets", "description": "Find semantically similar assets (text-based, vector search coming soon)", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Style or concept description"}}, "required": ["query"]}},
        {"name": "collection_stats", "description": "Get statistics about the entire artifact collection", "parameters": {"type": "object", "properties": {}}},
    ]

    mem_db.init()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            mid = msg.get("id", 0)
            method = msg.get("method", "")
            params = msg.get("params", {})

            if method == "initialize":
                resp = {"jsonrpc": "2.0", "id": mid, "result": {"serverInfo": {"name": "ai-artifact-memory", "version": "0.3.0"}, "capabilities": {"tools": {}}}}
            elif method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": mid, "result": {"tools": tools}}
            elif method == "tools/call":
                result = handle_call(params.get("name", ""), params.get("arguments", {}))
                resp = {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}}
            elif method == "notifications/initialized":
                continue
            else:
                resp = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}}

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except (json.JSONDecodeError, Exception):
            pass


if __name__ == "__main__":
    main()
