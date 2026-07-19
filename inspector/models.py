"""Unified data models for AI artifacts.

Artifact: top-level container for any AI-generated file.
Supports images, videos, 3D models, and more.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class LoraRef:
    name: str = ""
    weight: float = 0.0


@dataclass
class GenerationInfo:
    """Parameters used to generate this artifact."""
    model: str = ""
    model_hash: str = ""
    prompt: str = ""
    negative_prompt: str = ""
    seed: int = -1
    cfg: float = 0.0
    sampler: str = ""
    steps: int = 0
    width: int = 0
    height: int = 0
    loras: list[LoraRef] = field(default_factory=list)


@dataclass
class Artifact:
    """Top-level container for any AI-generated file."""
    path: str = ""
    file_type: str = ""          # "image", "video", "3d", "audio"
    source_tool: str = ""        # "ComfyUI", "A1111", "Midjourney", "DALL-E"
    file_size: int = 0
    generation: Optional[GenerationInfo] = None
    workflow_json: str = ""      # Raw workflow JSON if available
    parser_name: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Artifact":
        gen_data = data.get("generation")
        if gen_data:
            loras = [LoraRef(**l) for l in gen_data.pop("loras", [])]
            data["generation"] = GenerationInfo(**gen_data, loras=loras)
        return cls(**data)
