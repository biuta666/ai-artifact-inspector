# I Found a Hidden Layer Inside AI Images

*The PNG file was quietly storing the entire workflow.*

---

A few weeks ago, I found an image I had generated that I really liked.

The problem was: I had no idea how I made it.

I didn't remember the model. The LoRA. The prompt. The seed.

I assumed the workflow was lost.

Then I opened the PNG file.

Inside was something I didn't expect.

## The File Knew More Than I Did

The image was carrying its own production history.

Buried inside the PNG metadata was the complete generation record:

- The exact checkpoint model name
- The prompt and negative prompt
- Every LoRA and its weight
- The seed value
- The sampler and scheduler settings
- The CFG scale and step count
- In some cases, the full workflow graph

The image was not just an image. It was a self-contained archive of everything that created it.

And there was no way to read it back.

## Opening the Container

Most developers know that PNG files can store text metadata. That's how cameras embed EXIF data, and how Photoshop saves layer info.

AI generation tools like ComfyUI and AUTOMATIC1111 use the same mechanism.

When you generate an image, the tool writes its entire internal state into the file. The workflow JSON, the prompt text, the model references — it's all there, stored in standard PNG text chunks.

The data has been there the whole time. It just wasn't easy to extract.

## What I Did About It

I built a small tool that reads this hidden layer and reconstructs what it finds.

`ash
pip install ai-artifact-inspector
artifact inspect generated_image.png
`

It prints everything the file knows about itself:

`
File:     generated_image.png
Source:   ComfyUI

Generation:
  Model:   sd_xl_base_1.0
  Prompt:  cyberpunk girl in rain, neon lights, 8k
  Seed:    88392147
  Steps:   20
  CFG:     7.0
  LoRA:    neon_style_v2 (0.8)
`

It can also reconstruct the workflow graph from the same data:

`ash
artifact inspect generated_image.png --graph
`

This outputs a visual diagram of the generation pipeline. A single PNG becomes a readable map of how it was created.

Everything runs locally. No uploads, no cloud.

## What It Can Currently Understand

Right now it reads ComfyUI PNGs and AUTOMATIC1111 outputs. It can scan entire directories at once and export results as JSON.

## Why This Matters

I think we're at the beginning of a shift in how we think about generated files.

An image created by a human with a camera is a final output. What matters is what's in the frame.

An image created by an AI is different. The output is only half of what matters. The other half is the process — the model, the parameters, the seed, the workflow.

That information is currently hidden inside the file format, invisible to the person looking at the image.

In the future, we may not think of an AI image as a final output at all. We may think of it as an artifact — something that contains both the result and the complete process that created it.

This tool is a small step toward making that visible.

---

https://github.com/biuta666/ai-artifact-inspector

*MIT. Zero dependencies. All local.*