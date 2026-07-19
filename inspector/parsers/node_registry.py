"""Node Registry - Maps ComfyUI class_types to extraction handlers.

Each handler knows how to extract specific parameters from a node.
Add new node types by registering a handler function, no parser changes needed.
"""

# Registry of (class_type, field_name) -> semantic meaning
# Used by the node scanner to extract parameters from any workflow

MODEL_NODES = [
    ("CheckpointLoaderSimple", "ckpt_name"),
    ("CheckpointLoader", "ckpt_name"),
    ("UNETLoader", "unet_name"),
    ("ImageOnlyCheckpointLoader", "ckpt_name"),
]

PROMPT_NODES = [
    ("CLIPTextEncode", "text"),
]

SEED_NODES = [
    ("KSampler", "seed"),
    ("KSamplerAdvanced", "seed"),
    ("RandomNoise", "noise_seed"),
]

SAMPLER_NODES = [
    ("KSampler", "sampler_name"),
    ("KSamplerAdvanced", "sampler_name"),
    ("KSamplerSelect", "sampler_name"),
]

STEPS_NODES = [
    ("KSampler", "steps"),
    ("KSamplerAdvanced", "steps"),
    ("BasicScheduler", "steps"),
]

CFG_NODES = [
    ("KSampler", "cfg"),
    ("KSamplerAdvanced", "cfg"),
]

LORA_NODES = [
    "LoraLoader",
    "LoraLoaderModelOnly",
]

LORA_FIELDS = ["lora_name", "strength_model", "strength_clip"]

WIDTH_NODES = [
    ("EmptyLatentImage", "width"),
    ("EmptySD3LatentImage", "width"),
]

HEIGHT_NODES = [
    ("EmptyLatentImage", "height"),
    ("EmptySD3LatentImage", "height"),
]


def get_all_handlers():
    """Return a dict of all registered handlers for inspection."""
    return {
        "model": MODEL_NODES,
        "prompt": PROMPT_NODES,
        "seed": SEED_NODES,
        "sampler": SAMPLER_NODES,
        "steps": STEPS_NODES,
        "cfg": CFG_NODES,
        "lora": LORA_NODES,
        "lora_fields": LORA_FIELDS,
        "width": WIDTH_NODES,
        "height": HEIGHT_NODES,
    }
