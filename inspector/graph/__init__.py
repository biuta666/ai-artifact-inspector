from .schema import ArtifactInfo
from .builder import build_from_artifact, to_topology_list
from .renderer import render_svg, render_topology_svg

def generate(workflow_json, title="Workflow"):
    if not workflow_json:
        return _empty(title)
    from ..models import Artifact
    a = Artifact(path="", file_type="image", workflow_json=workflow_json)
    info = build_from_artifact(a)
    if info.workflow and info.workflow.nodes:
        return render_svg(info, title)
    tl = to_topology_list(info)
    if tl:
        return render_topology_svg(tl, title)
    return _empty(title)

def _empty(title):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="288" height="60"><rect width="100%" height="100%" fill="#0d1117"/><text x="20" y="30" fill="#8b949e" font-family="monospace" font-size="12">' + title + ': No workflow data</text></svg>'