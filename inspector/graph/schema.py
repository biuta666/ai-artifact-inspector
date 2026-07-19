"""Universal Artifact Schema definitions.

Defines the standard structure for any AI-generated artifact.
All parsers output this schema. All downstream tools consume it.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ModelComponent:
    """Model used for generation."""
    name: str = ""
    hash: str = ""


@dataclass
class PromptData:
    """Prompt pair used in generation."""
    positive: str = ""
    negative: str = ""


@dataclass
class GenerationParameters:
    """Core generation parameters."""
    seed: int = -1
    steps: int = 0
    cfg: float = 0.0
    sampler: str = ""
    scheduler: str = ""
    width: int = 0
    height: int = 0


@dataclass
class ArtifactComponent:
    """A component used in the generation pipeline (LoRA, ControlNet, etc)."""
    type: str = ""          # "lora", "controlnet", "embedding", "hypernetwork"
    name: str = ""
    weight: float = 0.0


@dataclass
class WorkflowNode:
    """A single node in the generation workflow."""
    id: int = 0
    class_type: str = ""
    title: str = ""
    inputs: dict = field(default_factory=dict)
    outputs: list = field(default_factory=list)


@dataclass
class WorkflowEdge:
    """A connection between two workflow nodes."""
    source: int = 0
    source_output: int = 0
    target: int = 0
    target_input: int = 0


@dataclass
class WorkflowGraph:
    """Full workflow graph structure."""
    nodes: list = field(default_factory=list)
    edges: list = field(default_factory=list)


@dataclass
class ArtifactSource:
    """Source information about the artifact."""
    platform: str = ""        # "comfyui", "a1111", etc.
    version: str = ""


@dataclass
class ArtifactFile:
    """Physical file information."""
    path: str = ""
    size: int = 0
    created: str = ""
    hash: str = ""


@dataclass
class ArtifactInfo:
    """Top-level Universal Artifact Schema. Used by all tools in the chain."""
    artifact_id: str = ""
    type: str = ""                # "image", "video", "3d", "audio"
    source: Optional[ArtifactSource] = None
    creation_model: Optional[ModelComponent] = None
    prompt: Optional[PromptData] = None
    parameters: Optional[GenerationParameters] = None
    components: list = field(default_factory=list)
    workflow: Optional[WorkflowGraph] = None
    file: Optional[ArtifactFile] = None
    semantic: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ArtifactInfo":
        def _build(kls, d):
            if d is None:
                return None
            return kls(**d)
        return cls(
            artifact_id=data.get("artifact_id", ""),
            type=data.get("type", ""),
            source=_build(ArtifactSource, data.get("source")),
            creation_model=_build(ModelComponent, data.get("creation_model")),
            prompt=_build(PromptData, data.get("prompt")),
            parameters=_build(GenerationParameters, data.get("parameters")),
            components=[ArtifactComponent(**c) for c in data.get("components", [])],
            workflow=_build(WorkflowGraph, data.get("workflow")) if data.get("workflow") else None,
            file=_build(ArtifactFile, data.get("file")),
            semantic=data.get("semantic", {}),
        )

    @classmethod
    def from_legacy(cls, artifact) -> "ArtifactInfo":
        """Convert old Artifact model to new Universal Schema."""
        info = cls(type="image")
        gen = artifact.generation
        if gen:
            info.creation_model = ModelComponent(name=gen.model, hash=getattr(gen, "model_hash", ""))
            info.prompt = PromptData(positive=gen.prompt, negative=gen.negative_prompt)
            info.parameters = GenerationParameters(
                seed=gen.seed, steps=gen.steps, cfg=gen.cfg, sampler=gen.sampler,
            )
            for lora in gen.loras:
                info.components.append(ArtifactComponent(type="lora", name=lora.name, weight=lora.weight))
        info.source = ArtifactSource(platform=artifact.source_tool)
        info.file = ArtifactFile(path=artifact.path, size=artifact.file_size)
        return info
