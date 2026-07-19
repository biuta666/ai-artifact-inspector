import struct, json, os
from ..parser import BaseParser, register
from ..models import Artifact, GenerationInfo, LoraRef

def _read_png_chunks(path):
    result = {}
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            return result
        while True:
            header = f.read(8)
            if len(header) < 8:
                break
            length = struct.unpack('>I', header[:4])[0]
            chunk_type = header[4:8].decode('latin-1', errors='replace')
            data = f.read(length)
            if len(data) < length:
                break
            if chunk_type in ('tEXt', 'iTXt', 'zTXt'):
                null_pos = data.find(b'\x00')
                if null_pos >= 0:
                    key = data[:null_pos].decode('latin-1', errors='replace')
                    value = data[null_pos + 1:].decode('latin-1', errors='replace')
                    result[key] = value
            f.read(4)
    return result

def _parse_comfyui_workflow(workflow_json):
    gen = GenerationInfo()
    try:
        workflow = json.loads(workflow_json)
    except json.JSONDecodeError:
        return gen
    if "nodes" in workflow:
        nodes = {n["id"]: n for n in workflow["nodes"]}
    else:
        nodes = workflow
    prompts = []
    negatives = []
    for nid, node in nodes.items():
        if isinstance(node, dict):
            ct = node.get("class_type", "")
            if ct == "CLIPTextEncode":
                text = str(node.get("inputs", {}).get("text", ""))
                meta = node.get("_meta", {})
                title = meta.get("title", "") if isinstance(meta, dict) else ""
                if "neg" in title.lower() or "negative" in title.lower():
                    negatives.append(text)
                else:
                    prompts.append(text)
    gen.prompt = prompts[0] if prompts else ""
    gen.negative_prompt = negatives[0] if negatives else ""
    for nid, node in nodes.items():
        if isinstance(node, dict):
            ct = node.get("class_type", "")
            if "CheckpointLoader" in ct or "ModelLoader" in ct:
                inp = node.get("inputs", {})
                ckpt = str(inp.get("ckpt_name", inp.get("model_name", "")))
                gen.model = os.path.splitext(ckpt)[0]
                break
    for nid, node in nodes.items():
        if isinstance(node, dict):
            ct = node.get("class_type", "")
            if "LoraLoader" in ct:
                inp = node.get("inputs", {})
                name = str(inp.get("lora_name", ""))
                w = float(inp.get("strength_model", 0.0))
                gen.loras.append(LoraRef(name=os.path.splitext(name)[0], weight=w))
    for nid, node in nodes.items():
        if isinstance(node, dict):
            ct = node.get("class_type", "")
            if "KSampler" in ct or ct == "SamplerCustom":
                inp = node.get("inputs", {})
                gen.seed = int(inp.get("seed", -1))
                gen.cfg = float(inp.get("cfg", 0.0))
                gen.sampler = str(inp.get("sampler_name", ""))
                gen.steps = int(inp.get("steps", 0))
    return gen

def _parse_a1111_params(text):
    gen = GenerationInfo()
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("Prompt:"):
            gen.prompt = line[7:].strip()
        elif line.startswith("Negative prompt:"):
            gen.negative_prompt = line[16:].strip()
        elif line.startswith("Steps:"):
            try: gen.steps = int(line.split(",")[0].split(":")[1].strip())
            except: pass
        elif line.startswith("Seed:"):
            try: gen.seed = int(line.split(",")[0].split(":")[1].strip())
            except: pass
        elif line.startswith("CFG scale:"):
            try: gen.cfg = float(line.split(",")[0].split(":")[1].strip())
            except: pass
        elif line.startswith("Model:"):
            gen.model = line.split(":")[1].strip()
        elif line.startswith("Sampler:"):
            gen.sampler = line.split(":")[1].strip()
    return gen

@register
class PNGParser(BaseParser):
    def name(self):
        return "PNG Metadata Parser"
    def can_parse(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext != ".png" or not os.path.isfile(path):
            return False
        with open(path, "rb") as f:
            sig = f.read(8)
        return sig == b'\x89PNG\r\n\x1a\n'
    def parse(self, path):
        artifact = Artifact(path=path, file_type="image", parser_name=self.name())
        artifact.file_size = os.stat(path).st_size
        chunks = _read_png_chunks(path)
        workflow_json = ""
        for key in ["workflow", "prompt"]:
            if key in chunks:
                workflow_json = chunks[key]
                break
        if workflow_json:
            artifact.source_tool = "ComfyUI"
            artifact.generation = _parse_comfyui_workflow(workflow_json)
            artifact.workflow_json = workflow_json
            return artifact
        params = None
        for k in ["parameters", "Description", "Comment"]:
            if k in chunks:
                params = chunks[k]
                break
        if params:
            artifact.source_tool = "A1111"
            artifact.generation = _parse_a1111_params(params)
            return artifact
        artifact.source_tool = "Unknown"
        gen = GenerationInfo()
        for key, val in chunks.items():
            kl = key.lower()
            if "prompt" in kl: gen.prompt = val[:500]
            elif "model" in kl or "checkpoint" in kl: gen.model = val[:100]
            elif "seed" in kl:
                try: gen.seed = int(val)
                except: pass
        artifact.generation = gen
        return artifact