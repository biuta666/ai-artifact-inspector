"""Workflow graph generator - Converts ComfyUI workflow JSON to SVG."""
import json


def generate(workflow_json, title="Workflow"):
    """Generate an SVG flowchart from a ComfyUI workflow JSON."""
    try:
        workflow = json.loads(workflow_json)
    except (json.JSONDecodeError, TypeError):
        return _empty_graph(title)

    # Parse nodes
    nodes = []
    for nid, node in workflow.items():
        if isinstance(node, dict):
            ct = node.get("class_type", "Unknown")
            nodes.append({"id": str(nid), "type": ct})

    if not nodes:
        return _empty_graph(title)

    # Layout
    box_w, box_h = 220, 40
    gap = 20
    svg_w = box_w + 40
    svg_h = len(nodes) * (box_h + gap) + 30

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}">',
        f'  <rect width="100%" height="100%" fill="#0d1117"/>',
        f'  <text x="20" y="24" fill="#58a6ff" font-family="monospace" font-size="14" font-weight="bold">{title}</text>',
    ]

    for i, node in enumerate(nodes):
        y = 36 + i * (box_h + gap)
        # Box
        lines.append(f'  <rect x="20" y="{y}" width="{box_w}" height="{box_h}" rx="6" fill="#161b22" stroke="#30363d" stroke-width="1"/>')
        # Arrow
        if i < len(nodes) - 1:
            ay = y + box_h
            lines.append(f'  <line x1="{box_w // 2 + 20}" y1="{ay}" x2="{box_w // 2 + 20}" y2="{ay + gap}" stroke="#30363d" stroke-width="2"/>')
            lines.append(f'  <polygon points="{box_w // 2 + 16},{ay + gap - 4} {box_w // 2 + 24},{ay + gap - 4} {box_w // 2 + 20},{ay + gap}" fill="#30363d"/>')
        # Icon
        lines.append(f'  <circle cx="42" cy="{y + box_h // 2}" r="5" fill="#238636"/>')
        # Text
        t = node["type"][:28]
        lines.append(f'  <text x="56" y="{y + box_h // 2 + 5}" fill="#e6edf3" font-family="monospace" font-size="12">{t}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def _empty_graph(title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="260" height="60">\n'
        f'  <rect width="100%" height="100%" fill="#0d1117"/>\n'
        f'  <text x="20" y="30" fill="#8b949e" font-family="monospace" font-size="12">{title}: No workflow data</text>\n'
        f'</svg>'
    )
