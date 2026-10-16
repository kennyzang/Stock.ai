"""Build FLUX.2 klein 9B (ComfyUI) jobs for episode 06 reference images.

Replaces the old ChatGPT/Codex `make_refs.sh` (not available on the server). Earlier episodes' sheets are
attached as STYLE references so the ink-wash look stays consistent. Prompts describe only what should be there.

Run:  python make_refs.py [name ...]   -> jobs/*.api.json + order.txt (all, or only the named ones, new seeds)
Then on the server:  /root/run_episode.sh jobs/idiom-ep06-refs
Outputs: ComfyUI output/idiom_ep06/refs/<name>_00001_.png  -> copy to ComfyUI input/idioms/ep06_<name>.png
"""
import json, random, sys
from pathlib import Path

OUT = Path(__file__).parent / "jobs"
OUT.mkdir(exist_ok=True)

UNET = "idiom_flux2_klein_9b_kv_fp8.safetensors"
CLIP = "idiom_qwen_3_8b_fp8mixed.safetensors"
VAE = "idiom_flux2-vae.safetensors"

STYLE = ("Traditional Chinese ink-wash painting (shuimo) on warm aged rice paper, loose expressive black ink brushstrokes, "
         "soft grey washes, lots of open space, muted earthy colors with small vermilion red accents. Slightly stylized and a bit "
         "humorous, like a hand-painted storybook, in exactly the same painting style as the reference images. "
         "Plain clean surfaces. No text, no letters, no calligraphy, no signature, no seal stamps.")

# style refs already on the server (ComfyUI input/)
CAT = "idioms/04_mascot_cat_sheet.png"
RIVER = "idioms/ep04_01_river.png"
STYLE06 = "idioms/ep06_01_style_frame.png"  # generated first (01), used as the style ref for the sheets
SCHOLAR = "idioms/ep06_02_scholar_sheet.png"   # generated below, then reused for the other sheets

V, L = (768, 1344), (1344, 768)
SHEET = ("Landscape 16:9 character sheet on a plain rice-paper background, like the reference character sheet: the same person "
         "shown as a front view, a side view and a back view standing in a row, plus a few action poses, all on blank paper. ")

JOBS = [
    ("01_style_frame", V, [RIVER, CAT],
     f"Vertical 9:16 master scene. {STYLE} Scene: a quiet country road in ancient China on a hot summer day. On the left of the road "
     "a melon field with large round green striped watermelons lying on leafy vines; further down the road on the right, one single "
     "plum tree heavy with ripe purple plums. A low earth wall and distant soft hills. Nobody in the scene. The upper third of the "
     "picture is open pale sky."),
    ("02_scholar_sheet", L, [STYLE06, CAT],  # not ep04's sheet (its bearded man leaked in); kept seed variant showed no cat traits
     f"{SHEET}{STYLE} Character: a YOUNG TRAVELING SCHOLAR of ancient China, about twenty: slim, beardless, kind face, wearing a "
     "pale blue robe, a small black scholar cap, straw sandals, a small cloth bundle tied on his back. Poses: walking with the bundle; "
     "crouching down to retie a sandal strap with both hands; standing with both empty hands open in front of him, embarrassed; "
     "raising both hands to straighten his cap. Every figure is this SAME young beardless man with the same pale blue robe, "
     "black cap and bundle; there is no other person on the sheet. The paper is completely blank around the figures."),
    ("03_farmer_sheet", L, [STYLE06, SCHOLAR],  # no cat sheet: cat ears/tails leak into human figures
     f"{SHEET}{STYLE} Character: a MELON FARMER of ancient China in his forties: stocky and broad, bald head with a brown cloth "
     "headband, round tanned face, thick eyebrows, short brown jacket, rolled-up trousers, barefoot, holding a wooden hoe. Poses: "
     "standing with the hoe; frowning and pointing angrily; running with the hoe raised. Same face and clothes in every pose. "
     "He looks clearly different from the young scholar in the reference."),
    ("04_granny_sheet", L, [STYLE06, SCHOLAR],
     f"{SHEET}{STYLE} Character: a small OLD WOMAN of ancient China, about seventy: short and thin, grey hair in a neat bun, wrinkled "
     "kind face, dark green dress with a plum-red apron, carrying a round bamboo basket. Poses: walking with the basket; stopping "
     "with eyes wide in surprise; pointing up with one hand. Same face and clothes in every pose. She looks clearly different from "
     "the young scholar in the reference."),
]


def job(name, size, refs, text, seed):
    w, h = size
    p = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "FluxKVCache", "inputs": {"model": ["1", 0]}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "flux2", "device": "default"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["3", 0]}},
        "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
        "7": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "8": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": w, "height": h}},
        "9": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "10": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["4", 0]}},
        "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": f"idiom_ep06/refs/{name}"}},
    }
    pos, neg = ["5", 0], ["6", 0]
    for i, ref in enumerate(refs):
        b = 20 + 10 * i
        p[str(b)] = {"class_type": "LoadImage", "inputs": {"image": ref}}
        p[str(b + 1)] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": [str(b), 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 1}}
        p[str(b + 2)] = {"class_type": "VAEEncode", "inputs": {"pixels": [str(b + 1), 0], "vae": ["4", 0]}}
        p[str(b + 3)] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": pos, "latent": [str(b + 2), 0]}}
        p[str(b + 4)] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": neg, "latent": [str(b + 2), 0]}}
        pos, neg = [str(b + 3), 0], [str(b + 4), 0]
    p["11"] = {"class_type": "CFGGuider", "inputs": {"model": ["2", 0], "positive": pos, "negative": neg, "cfg": 1.0}}
    p["12"] = {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["10", 0], "guider": ["11", 0], "sampler": ["9", 0], "sigmas": ["8", 0], "latent_image": ["7", 0]}}
    return {"prompt": p, "client_id": f"idiom-ep06-ref-{name}"}


if __name__ == "__main__":
    only = sys.argv[1:]
    names = []
    for name, size, refs, text in JOBS:
        if only and not any(name.startswith(o) for o in only):
            continue
        seed = random.randint(1, 2**31) if only else 606000 + len(names)
        (OUT / f"{name}.api.json").write_text(json.dumps(job(name, size, refs, text, seed), ensure_ascii=False, indent=1), encoding="utf-8")
        names.append(name)
    (OUT / "order.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"{len(names)} jobs: {names}")
