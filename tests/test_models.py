"""Model tests."""
from inspector.models import Artifact, GenerationInfo, LoraRef


class TestModels:
    def test_generation_defaults(self):
        g = GenerationInfo()
        assert g.model == ""
        assert g.seed == -1
        assert g.loras == []

    def test_generation_with_loras(self):
        g = GenerationInfo(
            model="SDXL",
            prompt="test",
            seed=42,
            loras=[LoraRef(name="style", weight=0.8)]
        )
        assert g.model == "SDXL"
        assert g.seed == 42
        assert g.loras[0].name == "style"

    def test_artifact_defaults(self):
        a = Artifact()
        assert a.file_type == ""
        assert a.generation is None

    def test_artifact_with_generation(self):
        g = GenerationInfo(model="SDXL", prompt="test")
        a = Artifact(path="/test.png", file_type="image", source_tool="ComfyUI", generation=g)
        assert a.source_tool == "ComfyUI"
        assert a.generation.model == "SDXL"

    def test_to_dict_roundtrip(self):
        g = GenerationInfo(model="SDXL", prompt="test", loras=[LoraRef("lora1", 0.5)])
        a = Artifact(path="/test.png", file_type="image", source_tool="ComfyUI", generation=g)
        d = a.to_dict()
        assert d["file_type"] == "image"
        assert d["generation"]["model"] == "SDXL"
        assert d["generation"]["loras"][0]["name"] == "lora1"

        a2 = Artifact.from_dict(d)
        assert a2.file_type == "image"
        assert a2.generation.model == "SDXL"
        assert a2.generation.loras[0].name == "lora1"
