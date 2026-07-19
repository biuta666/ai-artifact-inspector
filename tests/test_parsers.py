import os, tempfile, struct, zlib
from inspector.parser import registry
from inspector.parsers import png

def _make_minimal_png(text_chunks=None):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data
    ihdr += struct.pack('>I', zlib.crc32(ihdr[4:]) & 0xffffffff)
    chunks = [sig, ihdr]
    if text_chunks:
        for key, val in text_chunks.items():
            raw = key.encode('latin-1') + b'\x00' + val.encode('latin-1')
            c = struct.pack('>I', len(raw)) + b'tEXt' + raw
            c += struct.pack('>I', zlib.crc32(c[4:]) & 0xffffffff)
            chunks.append(c)
    iend = struct.pack('>I', 0) + b'IEND'
    iend += struct.pack('>I', zlib.crc32(iend[4:]) & 0xffffffff)
    chunks.append(iend)
    return b''.join(chunks)

class TestPNGParser:
    def test_can_parse_png(self):
        data = _make_minimal_png()
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(data)
            path = f.name
        parser = registry.find(path)
        os.unlink(path)
        assert parser is not None
        assert parser.name() == "PNG Metadata Parser"

    def test_cannot_parse_txt(self):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'hello')
            path = f.name
        parser = registry.find(path)
        os.unlink(path)
        assert parser is None

    def test_parse_comfyui_workflow(self):
        workflow = '{"6": {"class_type": "CLIPTextEncode", "inputs": {"text": "a cat"}}, "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "bad"}}, "3": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl.safetensors"}}, "5": {"class_type": "KSampler", "inputs": {"seed": 42, "cfg": 7, "sampler_name": "euler", "steps": 20}}}'
        data = _make_minimal_png({"workflow": workflow, "prompt": workflow})
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(data)
            path = f.name
        result = registry.parse(path)
        os.unlink(path)
        assert result is not None
        assert result.source_tool == "ComfyUI"
        gen = result.generation
        assert gen is not None
        assert gen.model == "sd_xl"
        assert gen.seed == 42
        assert gen.cfg == 7.0
        assert gen.sampler == "euler"
        assert gen.steps == 20
        assert gen.prompt == "a cat"