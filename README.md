# AI Artifact Inspector

> **Understand any AI-generated file. Reveal its full production pipeline.**

Drop in any AI-generated image → instantly see the model, prompt, seed, LoRA, and workflow behind it.

\\\ash
pip install ai-artifact-inspector
artifact inspect samples/comfyui_cyberpunk.png
\\\

## Demo

\\\
$ artifact inspect samples/comfyui_cyberpunk.png

File:     samples/comfyui_cyberpunk.png
Type:     image
Source:   ComfyUI
Parser:   PNG Metadata Parser
Size:     1,101 bytes

Generation:
  Model:   sd_xl_base_1.0
  Prompt:  a cyberpunk girl in rain, neon lights, 8k
  Neg:     ugly, blurry, low quality
  Seed:    1234567890
  Steps:   20
  CFG:     7.0
  Sampler: euler

No cloud. No upload. Your files stay local.
\\\

## Why

Every day, millions of AI-generated images are created. The **know-how** behind each image is trapped inside the file — in PNG metadata chunks, ComfyUI workflow JSON, and binary blobs.

**AI Artifact Inspector** extracts this knowledge:

- **Creators** → recover past prompts, models, and settings
- **Learners** → understand how a specific effect was achieved
- **Teams** → audit and archive production assets

## Quick Start

\\\ash
# Install
pip install ai-artifact-inspector

# Try it with the sample
artifact inspect samples/comfyui_cyberpunk.png

# Inspect your own files
artifact inspect your_image.png

# Full JSON output
artifact inspect your_image.png --verbose
\\\

## Supported Formats

| Format | Status | Details |
|--------|--------|---------|
| ComfyUI PNG | ✅ | Full workflow, nodes, prompts, model, LoRA |
| AUTOMATIC1111 PNG | ✅ | Prompt, negative, seed, model, params |
| Midjourney | 📅 | Prompt, style, version |
| DALL-E | 📅 | Metadata extraction |
| AI Video | 📅 | Frame-by-frame analysis |
| 3D Models | 📅 | Generation parameters |

## Architecture

\\\
Any AI File → Parser Router → [PNG | MJ | Video ...] → Artifact Model → CLI / JSON
\\\

The system is designed to be extended. Each format gets its own parser implementing a simple interface.

## Extending

Add a new parser in 3 steps:

\\\python
from inspector.parser import BaseParser, register
from inspector.models import Artifact

@register
class MyParser(BaseParser):
    def name(self):
        return "My Format Parser"

    def can_parse(self, path):
        return path.endswith(".myfmt")

    def parse(self, path):
        return Artifact(...)
\\\

## Development

\\\ash
git clone https://github.com/biuta666/ai-artifact-inspector
cd ai-artifact-inspector
pip install -e .
pip install pytest
python -m pytest tests/
\\\

## License

MIT