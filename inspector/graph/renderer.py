from .builder import to_topology_list

BG = "#0d1117"
NBG = "#161b22"
NBORD = "#30363d"
TP = "#e6edf3"
TS = "#8b949e"
AC = "#58a6ff"
GR = "#238636"
OR = "#d29922"

NW = 240
NH = 36
GY = 24
M = 24

def render_svg(info, title="Workflow"):
    if info.workflow and info.workflow.nodes:
        return _render_wf(info.workflow.nodes, info.workflow.edges, title)
    return render_topology_svg(to_topology_list(info), title)

def render_topology_svg(items, title="Workflow"):
    if not items:
        return _empty("No workflow data", title)
    sw = NW + M * 2
    sh = M * 2 + len(items) * (NH + GY)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(sw) + '" height="' + str(sh) + '">',
        '  <rect width="100%" height="100%" fill="' + BG + '"/>',
        '  <text x="' + str(M) + '" y="' + str(M + 14) + '" fill="' + AC + '" font-family="monospace" font-size="13" font-weight="bold">' + title + '</text>',
    ]
    for i, item in enumerate(items):
        y = M * 2 + i * (NH + GY)
        if i > 0:
            mx = M + NW // 2
            lines.append('  <line x1="' + str(mx) + '" y1="' + str(y - GY) + '" x2="' + str(mx) + '" y2="' + str(y - 4) + '" stroke="' + NBORD + '" stroke-width="1.5"/>')
            lines.append('  <polygon points="' + str(mx - 4) + ',' + str(y - 8) + ' ' + str(mx + 4) + ',' + str(y - 8) + ' ' + str(mx) + ',' + str(y - 2) + '" fill="' + NBORD + '"/>')
        color = _tc(item.get("type", ""))
        lines.append('  <rect x="' + str(M) + '" y="' + str(y) + '" width="' + str(NW) + '" height="' + str(NH) + '" rx="6" fill="' + NBG + '" stroke="' + color + '" stroke-width="1"/>')
        lines.append('  <circle cx="' + str(M + 18) + '" cy="' + str(y + NH // 2) + '" r="5" fill="' + color + '"/>')
        label = str(item.get("label", item.get("type", "")))[:45]
        lines.append('  <text x="' + str(M + 32) + '" y="' + str(y + NH // 2 + 5) + '" fill="' + TP + '" font-family="monospace" font-size="11">' + label + '</text>')
    lines.append("</svg>")
    return "\n".join(lines)

def _render_wf(nodes, edges, title):
    if not nodes:
        return _empty("No workflow data", title)
    sw = NW + M * 2
    sh = M * 2 + len(nodes) * (NH + GY)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(sw) + '" height="' + str(sh) + '">',
        '  <rect width="100%" height="100%" fill="' + BG + '"/>',
        '  <text x="' + str(M) + '" y="' + str(M + 14) + '" fill="' + AC + '" font-family="monospace" font-size="13" font-weight="bold">' + title + '</text>',
    ]
    for i, node in enumerate(nodes):
        y = M * 2 + i * (NH + GY)
        ct = str(getattr(node, "class_type", "Unknown"))[:35]
        if i > 0:
            mx = M + NW // 2
            lines.append('  <line x1="' + str(mx) + '" y1="' + str(y - GY) + '" x2="' + str(mx) + '" y2="' + str(y - 4) + '" stroke="' + NBORD + '" stroke-width="1.5"/>')
            lines.append('  <polygon points="' + str(mx - 4) + ',' + str(y - 8) + ' ' + str(mx + 4) + ',' + str(y - 8) + ' ' + str(mx) + ',' + str(y - 2) + '" fill="' + NBORD + '"/>')
        color = _tc(ct)
        lines.append('  <rect x="' + str(M) + '" y="' + str(y) + '" width="' + str(NW) + '" height="' + str(NH) + '" rx="6" fill="' + NBG + '" stroke="' + color + '" stroke-width="1"/>')
        lines.append('  <circle cx="' + str(M + 18) + '" cy="' + str(y + NH // 2) + '" r="5" fill="' + color + '"/>')
        lines.append('  <text x="' + str(M + 32) + '" y="' + str(y + NH // 2 + 5) + '" fill="' + TP + '" font-family="monospace" font-size="11">' + ct + '</text>')
    lines.append("</svg>")
    return "\n".join(lines)

def _tc(t):
    t = t.lower()
    if "checkpoint" in t or "model" in t: return AC
    if "clip" in t or "encode" in t: return GR
    if "lora" in t: return OR
    if "sampler" in t or "k" in t: return "#f78166"
    if "vae" in t: return "#bc8cff"
    if "output" in t or "save" in t or "image" in t: return GR
    if "prompt" in t: return GR
    if "negative" in t: return "#f85149"
    return TS

def _empty(msg, title):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(NW + M * 2) + '" height="60"><rect width="100%" height="100%" fill="' + BG + '"/><text x="' + str(M) + '" y="30" fill="' + TS + '" font-family="monospace" font-size="12">' + title + ': ' + msg + '</text></svg>'