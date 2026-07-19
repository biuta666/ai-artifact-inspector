"""PNG metadata parser for AI-generated images.
Supports ComfyUI (all workflow formats) and AUTOMATIC1111.
"""
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


def _node_scan(workflow, class_type, field_path=None):
    """Scan all workflow nodes for a given class_type and extract fields.
    
    Returns list of extracted values. Each value is either the field value
    (if field_path is a string key name) or the entire node inputs dict.
    """
    results = []
    for nid, node in workflow.items():
        if not isinstance(node, dict):
            continue
        ct = node.get("class_type", "")
        if ct == class_type:
            inputs = node.get("inputs", {})
            if field_path:
                val = inputs.get(field_path)
                if val is not None:
                    results.append(val)
            else:
                results.append(inputs)
    return results


def _node_scan_value(workflow, class_type, field):
    """Scan and return the first matching field value."""
    vals = _node_scan(workflow, class_type, field)
    return vals[0] if vals else None


def _parse_comfyui_workflow(workflow_json):
    """Parse ComfyUI workflow by scanning ALL nodes by class_type.
    Handles SD1.5/XL, Flux, and custom node formats."""
    gen = GenerationInfo()
    try:
        workflow = json.loads(workflow_json)
    except (json.JSONDecodeError, TypeError):
        return gen
    if not isinstance(workflow, dict):
        return gen

    # Model: CheckpointLoaderSimple, CheckpointLoader, UNETLoader, ImageOnlyCheckpointLoader
    model_names = _node_scan(workflow, "CheckpointLoaderSimple", "ckpt_name")
    model_names += _node_scan(workflow, "CheckpointLoader", "ckpt_name")
    model_names += _node_scan(workflow, "UNETLoader", "unet_name")
    model_names += _node_scan(workflow, "ImageOnlyCheckpointLoader", "ckpt_name")
    if model_names:
        gen.model = os.path.splitext(str(model_names[0]))[0]

    # Prompt
    prompts = _node_scan(workflow, "CLIPTextEncode", "text")
    if prompts:
        gen.prompt = prompts[0]

    # Negative prompt (look for titles containing "negative" or second CLIPTextEncode)
    neg_prompts = []
    for nid, node in workflow.items():
        if isinstance(node, dict) and node.get("class_type") == "CLIPTextEncode":
            meta = node.get("_meta", {})
            title = (meta.get("title", "") if isinstance(meta, dict) else "").lower()
            if "neg" in title or "negative" in title or "uncond" in title:
                text = node.get("inputs", {}).get("text", "")
                if text:
                    neg_prompts.append(text)
    if not neg_prompts and len(prompts) > 1:
        gen.negative_prompt = prompts[1]
    elif neg_prompts:
        gen.negative_prompt = neg_prompts[0]

    # Seed: KSampler, KSamplerAdvanced, RandomNoise
    seeds = _node_scan(workflow, "KSampler", "seed")
    seeds += _node_scan(workflow, "KSamplerAdvanced", "seed")
    seeds += _node_scan(workflow, "RandomNoise", "noise_seed")
    if seeds:
        try:
            gen.seed = int(seeds[0])
        except (ValueError, TypeError):
            pass

    # Sampler name: KSampler, KSamplerAdvanced, KSamplerSelect
    samplers = _node_scan(workflow, "KSampler", "sampler_name")
    samplers += _node_scan(workflow, "KSamplerAdvanced", "sampler_name")
    samplers += _node_scan(workflow, "KSamplerSelect", "sampler_name")
    if samplers:
        gen.sampler = str(samplers[0])

    # Steps: KSampler, KSamplerAdvanced, BasicScheduler
    steps = _node_scan(workflow, "KSampler", "steps")
    steps += _node_scan(workflow, "KSamplerAdvanced", "steps")
    steps += _node_scan(workflow, "BasicScheduler", "steps")
    if steps:
        try:
            gen.steps = int(steps[0])
        except (ValueError, TypeError):
            pass

    # CFG: KSampler, KSamplerAdvanced
    cfgs = _node_scan(workflow, "KSampler", "cfg")
    cfgs += _node_scan(workflow, "KSamplerAdvanced", "cfg")
    if cfgs:
        try:
            gen.cfg = float(cfgs[0])
        except (ValueError, TypeError):
            pass

    # LoRA: LoraLoader, LoraLoaderModelOnly
    for lora_inputs in _node_scan(workflow, "LoraLoader"):
        name = str(lora_inputs.get("lora_name", ""))
        sw = float(lora_inputs.get("strength_model", 0.0))
        if name:
            gen.loras.append(LoraRef(name=os.path.splitext(name)[0], weight=sw))
    for lora_inputs in _node_scan(workflow, "LoraLoaderModelOnly"):
        name = str(lora_inputs.get("lora_name", ""))
        sw = float(lora_inputs.get("strength_model", 0.0))
        if name:
            gen.loras.append(LoraRef(name=os.path.splitext(name)[0], weight=sw))

    # Image dimensions
    widths = _node_scan(workflow, "EmptyLatentImage", "width")
    widths += _node_scan(workflow, "EmptySD3LatentImage", "width")
    if widths:
        try:
            gen.width = int(widths[0])
        except (ValueError, TypeError):
            pass
    heights = _node_scan(workflow, "EmptyLatentImage", "height")
    heights += _node_scan(workflow, "EmptySD3LatentImage", "height")
    if heights:
        try:
            gen.height = int(heights[0])
        except (ValueError, TypeError):
            pass

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

        # Try ComfyUI format
        # Two possible chunk keys: "workflow" (full graph) and "prompt" (API format)
        # The "prompt" chunk has flat dict with class_type - what our parser expects
        # The "workflow" chunk has nodes array format - different structure
        prompt_json = chunks.get("prompt", "")
        workflow_json = chunks.get("workflow", "")
        
        # Use prompt chunk for parsing (it has the right format)
        if prompt_json:
            artifact.source_tool = "ComfyUI"
            artifact.generation = _parse_comfyui_workflow(prompt_json)
            artifact.workflow_json = workflow_json or prompt_json
            return artifact
        
        # Fallback: use workflow chunk (will attempt to parse, may be partial)
        if workflow_json:
            artifact.source_tool = "ComfyUI"
            artifact.generation = _parse_comfyui_workflow(workflow_json)
            artifact.workflow_json = workflow_json
            return artifact

        # Try A1111 format
        params = None
        for k in ["parameters", "Description", "Comment"]:
            if k in chunks:
                params = chunks[k]
                break
        if params:
            artifact.source_tool = "A1111"
            artifact.generation = _parse_a1111_params(params)
            return artifact

        # Generic fallback
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
