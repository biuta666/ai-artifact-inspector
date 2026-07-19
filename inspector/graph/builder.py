import json
from .schema import ArtifactInfo, WorkflowNode, WorkflowEdge, WorkflowGraph

def build_from_artifact(artifact):
    info = ArtifactInfo.from_legacy(artifact)
    if artifact.workflow_json:
        try:
            wf = _parse_comfyui_to_graph(json.loads(artifact.workflow_json))
            if wf:
                info.workflow = wf
        except (json.JSONDecodeError, TypeError):
            pass
    return info

def _parse_comfyui_to_graph(wf):
    if not wf:
        return None
    graph = WorkflowGraph()
    seen = {}
    for nid, node in wf.items():
        if not isinstance(node, dict):
            continue
        ct = node.get("class_type", "Unknown")
        if ct in seen:
            continue
        seen[ct] = True
        wfn = WorkflowNode(
            id=int(nid) if nid.isdigit() else hash(nid) % 10000,
            class_type=ct,
            title="",
            inputs=node.get("inputs", {}),
        )
        graph.nodes.append(wfn)

    eid = 0
    for nid, node in wf.items():
        if not isinstance(node, dict):
            continue
        for inp_name, inp_val in node.get("inputs", {}).items():
            if isinstance(inp_val, list) and len(inp_val) == 2:
                src = str(inp_val[0])
                tgt = nid
                if src in wf and tgt in wf:
                    graph.edges.append(WorkflowEdge(id=eid, source=int(src) if src.isdigit() else hash(src) % 10000, target=int(tgt) if tgt.isdigit() else hash(tgt) % 10000))
                    eid += 1
    return graph

def to_topology_list(info):
    items = []
    if info.creation_model and info.creation_model.name:
        items.append({"type": "model", "label": info.creation_model.name})
    if info.prompt and info.prompt.positive:
        items.append({"type": "prompt", "label": "Prompt (" + str(len(info.prompt.positive)) + " chars)"})
        if info.prompt.negative:
            items.append({"type": "negative", "label": "Negative prompt"})
    for c in info.components:
        items.append({"type": c.type, "label": c.type + ": " + c.name + " (" + str(c.weight) + ")"})
    if info.parameters:
        p = info.parameters
        if p.sampler:
            items.append({"type": "sampler", "label": "Sampler: " + str(p.sampler) + " | Steps: " + str(p.steps) + " | CFG: " + str(p.cfg) + " | Seed: " + str(p.seed)})
    items.append({"type": "output", "label": "Output Image"})
    return items