"""Generate 1000 synthetic AI images with realistic ComfyUI metadata for testing."""
import struct, zlib, json, os, random, time

OUT = "test_1000"
random.seed(42)

MODELS = ["sd_xl_base_1.0", "realisticVisionV51", "dreamshaper_8", "juggernautXL_v9", "epiCRealism", "meinaMix_v11", "counterfeitXL", "animagineXL"]
LORAS = [("neon_style_v2", 0.8), ("chinese_face_v3", 0.6), ("detailed_eyes", 0.5), ("fantasy_style", 0.9), ("anime_v3", 0.7), ("film_grain", 0.3), ("", 0)]
SAMPLERS = ["euler", "dpmpp_2m", "dpmpp_sde", "ddim", "uni_pc", "lcm"]
STYLES = [
    "cyberpunk girl in rain, neon lights, cinematic, 8k",
    "medieval castle, foggy morning, fantasy art, epic landscape",
    "portrait of warrior woman, armor, dramatic lighting",
    "ancient temple in jungle, overgrown ruins, sunlight",
    "sci-fi cityscape, flying cars, neon signs, synthwave",
    "traditional chinese painting style, mountains, mist",
    "steampunk inventor, goggles, brass machinery, workshop",
    "post-apocalyptic wasteland, abandoned buildings, sunset",
    "underwater city, coral architecture, bioluminescent, deep blue",
    "gothic cathedral interior, stained glass, candlelight, dark",
]

def make_png(text_chunks):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 512, 512, 8, 2, 0, 0, 0)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data
    ihdr += struct.pack('>I', zlib.crc32(ihdr[4:]) & 0xffffffff)
    rd = b'\x00' + b'\xff\xff\xff' * 512
    rd *= 512
    z = zlib.compress(rd)
    idat = struct.pack('>I', len(z)) + b'IDAT' + z
    idat += struct.pack('>I', zlib.crc32(idat[4:]) & 0xffffffff)
    ch = [sig, ihdr, idat]
    if text_chunks:
        for k, v in text_chunks.items():
            r = k.encode() + b'\x00' + v.encode()
            c = struct.pack('>I', len(r)) + b'tEXt' + r
            c += struct.pack('>I', zlib.crc32(c[4:]) & 0xffffffff)
            ch.append(c)
    ie = struct.pack('>I', 0) + b'IEND'
    ie += struct.pack('>I', zlib.crc32(ie[4:]) & 0xffffffff)
    ch.append(ie)
    return b''.join(ch)

# Generate structured test data
# Model A (sd_xl): 500 images, shared model
# Model B (realistic): 250 images
# Model C (dreamshaper): 150 images
# Model D (juggernaut): 100 images
# Plus shared LoRA groups and seed groups

print("Generating 1000 test images...")
start = time.time()

image_groups = [
    ("sd_xl_batch", MODELS[0], 500, [LORAS[0], LORAS[1]]),
    ("realistic_batch", MODELS[1], 250, [LORAS[2], LORAS[3]]),
    ("dreamshaper_batch", MODELS[2], 150, [LORAS[4], LORAS[5]]),
    ("juggernaut_batch", MODELS[3], 100, [LORAS[0], LORAS[4]]),
]

total = 0
shared_seed = 12345
for group_name, model, count, loras in image_groups:
    group_dir = os.path.join(OUT, group_name)
    os.makedirs(group_dir, exist_ok=True)
    for i in range(count):
        style = STYLES[i % len(STYLES)]
        neg = "ugly, blurry, low quality, deformed"
        lora = loras[i % len(loras)]
        seed = shared_seed + i  # Some images share nearby seeds
        sampler = SAMPLERS[i % len(SAMPLERS)]

        workflow = {
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": style}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg + ", nsfw"}},
            "3": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model + ".safetensors"}},
            "5": {"class_type": "KSampler", "inputs": {"seed": seed, "cfg": 7.0, "sampler_name": sampler, "steps": 30}},
        }
        if lora[0]:
            lora_id = str(100 + i % 3)
            workflow[lora_id] = {"class_type": "LoraLoader", "inputs": {"lora_name": lora[0] + ".safetensors", "strength_model": lora[1]}}
        workflow["8"] = {"class_type": "VAEDecode", "inputs": {}}
        workflow["9"] = {"class_type": "SaveImage", "inputs": {}}

        png = make_png({"workflow": json.dumps(workflow), "prompt": json.dumps(workflow)})
        fp = os.path.join(group_dir, f"img_{i+1:04d}.png")
        with open(fp, "wb") as f:
            f.write(png)
        total += 1

    print(f"  {group_name}: {count} images, model={model}")

elapsed = time.time() - start
print(f"\nTotal: {total} images in {elapsed:.1f}s ({total/elapsed:.0f} images/s)")
print(f"Size: {total * 180 // 1024}MB total")
