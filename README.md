# AI Artifact Inspector

> **Give AI agents memory of your creative assets.**

![CI](https://github.com/biuta666/ai-artifact-inspector/actions/workflows/test.yml/badge.svg)

A local-first artifact memory layer for AI-generated images and workflows.

Parse any AI-generated image → extract its DNA → index into searchable memory → let AI agents query it.

## Quick Start

```bash
# Parse a single image
artifact inspect generated_image.png

# Visualize its workflow graph
artifact inspect generated_image.png --graph

# Index your entire collection into artifact memory
artifact index ./ai_outputs/

# Search by model, prompt, or source
artifact search "cyberpunk neon"

# Start MCP server for Claude/Cursor/Continue
artifact mcp
```

## What It Does

| Layer | Capability | Status |
|-------|-----------|--------|
| **Parse** | Read model, prompt, seed, LoRA from PNG | ✅ |
| **Graph** | Visualize the complete workflow as SVG | ✅ |
| **Memory** | SQLite database, index/search/archive | ✅ |
| **MCP** | 5 tools for any MCP-compatible AI Agent | ✅ |
| **Understand** | Semantic understanding (Qwen) | 📅 v0.4 |
| **Doctor** | Quality diagnosis and optimization | 📅 v0.5 |

## Architecture

```
PNG → Parser → Schema → Graph → Memory Core → MCP → AI Agent
```

The chain turns a single image file into structured, queryable, Agent-accessible knowledge.

## Benchmark

### Real-World Parser Accuracy

Tested against the official ComfyUI example repository — 100 real images covering SDXL, Flux, SD3, ControlNet, and LoRA workflows.

| Metric | Result |
|--------|--------|
| ComfyUI detected | 100/100 (100%) |
| Model extracted | 91/100 (91%) |
| Prompt extracted | 83/100 (83%) |
| Seed extracted | 87/100 (87%) |
| Sampler extracted | 92/100 (92%) |
| Workflow JSON found | 92/100 (92%) |
| Unique models detected | 49 |
| Hard errors | 0 |

### Index & Search Performance (1000 Images)

| Metric | Result |
|--------|--------|
| Index speed | 20s for 1000 files (20ms/file) |
| Search speed | ~50ms (SQLite LIKE) |
| Auto-generated relations | 222,850 edges |
| Database size | 23MB (23KB per artifact) |
| Memory usage | < 500MB during indexing |

All parsing, indexing, and relation-building runs locally with zero external dependencies.

## MCP Tools (for AI Agents)

Start the server:

```bash
artifact mcp
```

Then Claude Desktop, Cursor, or Continue can call:

| Tool | Agent Says | Agent Gets |
|------|-----------|------------|
| `search_artifacts` | "Find my cyberpunk characters" | Matching assets with model/prompt/seed |
| `get_artifact` | "How was this one made?" | Full generation DNA |
| `get_workflow` | "Show me the node graph" | SVG workflow visualization |
| `similar_assets` | "Find more like this" | Similar style matches |
| `collection_stats` | "What do I have?" | Asset count by source/model |

## Install

```bash
pip install ai-artifact-inspector
```

Or build from source:

```bash
git clone https://github.com/biuta666/ai-artifact-inspector
cd ai-artifact-inspector
pip install -e .
```

## Development

```bash
pip install -e .
pip install pytest
python -m pytest tests/
```

## License

MIT

*No cloud. No upload. Your files stay local.*
