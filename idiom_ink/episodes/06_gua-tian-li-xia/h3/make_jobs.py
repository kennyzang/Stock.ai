"""Build MiniMax H3 reference-to-video ComfyUI API jobs for episode 06 (瓜田李下).

Copied from episode 05. Prompts only describe what SHOULD be on screen (this H3 setup has no real negative prompt),
sound cues are physical only. Two-person shots list the minor character's ref first and say "Exactly two people".
Refs were made with FLUX.2 klein on the server (see ../references/make_refs.py).
"""

import json
from pathlib import Path

EP = "ep06"
OUT = Path(__file__).parent / "jobs"
OUT.mkdir(exist_ok=True)

W, H, FPS = 768, 1344, 24
REF = {
    "road": "idioms/ep06_01_style_frame.png",
    "scholar": "idioms/ep06_02_scholar_sheet.png",
    "farmer": "idioms/ep06_03_farmer_sheet.png",
    "granny": "idioms/ep06_04_granny_sheet.png",
    "cat": "idioms/04_mascot_cat_sheet.png",
}
REF_DESC = {
    "road": "the set and painting-style reference: a quiet dusty country road in ancient China in summer, a melon field with big round green striped watermelons on leafy vines on one side, one plum tree full of purple plums beside a low earth wall, soft distant hills, painted in Chinese ink wash on aged rice paper",
    "scholar": "the character sheet of THE YOUNG SCHOLAR: a slim beardless young man with a kind face, in a pale blue robe with a red sash, a small black scholar cap, straw sandals and a small brown cloth bundle on his back",
    "farmer": "the character sheet of THE MELON FARMER: a stocky bald man with a red-brown cloth headband, thick eyebrows and a stern face, in a short brown jacket and baggy brown trousers, holding a long wooden hoe",
    "granny": "the character sheet of THE OLD WOMAN: a small thin old woman with grey hair in a bun and a wrinkled face, in a dark green dress with a plum-red apron, carrying one round bamboo basket",
    "cat": "the character sheet of the SCHOLAR CAT host: a small cute tabby cat in a grey scholar robe with a vermilion sash and a black scholar hat, holding a calligraphy brush",
}
SUBJECT = {
    "scholar": "the young scholar, exactly as drawn in {pic}: same beardless young face, pale blue robe, red sash, black cap and bundle in every frame",
    "farmer": "the melon farmer, exactly as drawn in {pic}: same bald head with headband, stern face, brown jacket and trousers in every frame",
    "granny": "the old woman, exactly as drawn in {pic}: same grey bun, wrinkled face, dark green dress and plum-red apron, carrying one basket, in every frame",
    "cat": "the scholar cat host, exactly as drawn in {pic}: same face, robe, vermilion sash, black hat and brush in every frame",
}
RETAIN = {
    "road": "keep the exact ink-wash style, the melon field, the plum tree and the dusty road.",
}

STYLE = (
    "Animated traditional Chinese ink-wash painting (shuimo) on warm aged rice paper: loose expressive black ink brushstrokes, "
    "soft grey washes, lots of open space, muted earthy colors. It looks like a hand-painted storybook coming to life, "
    "with gentle painterly motion. Characters are stylized painted figures."
)
CLEAN = (" The composition is clean and simple: plain ground, clear calm air, only the characters and objects described. "
         "Natural, unhurried, physically plausible motion; everyone stays fully inside the frame in one continuous shot.")
NEGATIVE = "No speech, no voices, no narration, no music."

# (id, refs, seconds, scene, soundscape)
SHOTS = [
    ("H1_hook", ["scholar", "farmer", "road"], 6,
     "Exactly two people in the melon field. In the middle of the field the slim young scholar crouches low among the big striped "
     "watermelons, both hands on his sandal strap, looking up surprised. At the edge of the field the stocky bald farmer stands "
     "with his hoe in one hand and points angrily at him with the other.",
     "Wind in leaves, rustling melon vines."),
    ("S02_road", ["scholar", "road"], 5,
     "The young scholar walks along the dusty country road under a hot sun, his small bundle on his back, and wipes his brow "
     "with his sleeve. The melon field is beside the road. Slow side tracking shot.",
     "Footsteps on a dirt road, cicadas."),
    ("S03_strap", ["scholar", "road"], 5,
     "At the edge of the melon field the young scholar stops walking; the strap of one straw sandal snaps and the sandal slips "
     "off his foot. He looks down at it and sighs, shoulders dropping.",
     "Footsteps stopping, a soft snap of straw."),
    ("S04_tie", ["scholar", "road"], 5,
     "Close-up: the young scholar crouches down between the melon vines and carefully ties his straw sandal strap with both "
     "hands. Big striped watermelons lie all around him.",
     "Rustling leaves, straw being tied."),
    ("S05_farmer_sees", ["scholar", "farmer", "road"], 5,
     "Exactly two people. Wide view from behind the stocky bald farmer standing on a path at the far end of the melon field: far "
     "away in the middle of the field only the bent back of the crouching young scholar shows among the melons. The farmer "
     "frowns and grips his hoe.",
     "Wind over the field."),
    ("S06_run", ["farmer", "road"], 5,
     "The stocky bald farmer runs along the path beside the melon field, holding his long wooden hoe up with both hands, angry.",
     "Heavy running footsteps on dirt."),
    ("S07_hands", ["farmer", "scholar", "road"], 5,
     "Exactly two people at the edge of the melon field. The young scholar stands up and shows both empty open hands; the "
     "stocky bald farmer glares at him with narrowed eyes, his hoe held across his body, not believing him.",
     "Wind, a hoe handle knocking softly on the ground."),
    ("S08_wind", ["scholar", "road"], 5,
     "Medium shot. Exactly one person in the whole scene: the young scholar stands still on the dusty road right under the "
     "plum tree heavy with purple plums, by the low earth wall; the rest of the road is empty. A gust of wind blows from the left: "
     "the leaves and plums sway, his sleeves flutter, and his black cap is pushed crooked, tilting to one side on his head. "
     "He looks up, surprised.",
     "Wind gusting through branches, leaves rustling."),
    ("S09_cap", ["scholar", "road"], 5,
     "Under the low branches of the plum tree, the young scholar raises both hands to his head and straightens his black cap; "
     "ripe purple plums hang just above his hands.",
     "Branches creaking softly, cloth rustling."),
    ("S10_granny", ["granny", "road"], 5,
     "On the dusty road near the plum tree the small old woman with her one bamboo basket stops walking, her eyes go wide and "
     "her mouth opens in shock, and she points up toward the plum tree.",
     "Footsteps stopping, a basket creaking."),
    ("S11_sunset", ["scholar", "road"], 5,
     "Exactly one person in the whole scene: the young scholar, seen from behind, walks slowly away along the empty dusty "
     "road in soft evening light, head bowed in thought, his small bundle on his back. He stays one single solid figure the "
     "whole time; the road ahead of him is empty. The melon field is on his left.",
     "Slow footsteps, evening birds."),
    ("P1_payoff", ["road"], 13,
     "Very wide, calm view of the country road, the melon field and the single plum tree at golden hour: the upper half of the "
     "frame is open pale sky; leaves sway gently in the wind. Nobody in the scene. Static camera.",
     "Soft wind, distant birds."),
    ("U1_cousin", ["cat"], 8,
     "The scholar cat stands in a simple, plain study with bare pale walls and a clean wooden floor, holds up one paw, "
     "palm out, politely shakes its head, and takes one small step back, as if stepping aside. The upper part of the frame "
     "is a plain, clean, empty pale wall; the air is clear and still.",
     "Soft paw steps on a wooden floor, cloth rustling."),
    ("U2_phone", ["cat"], 8,
     "The scholar cat stands very straight in a simple, plain study with bare pale walls and a clean wooden floor, holds up "
     "both empty paws in front of its chest to show there is nothing in them, with a small proud smile, tail swishing. The "
     "upper part of the frame is a plain, clean, empty pale wall; the air is clear and still.",
     "A soft tail swish, a quiet room."),
]


def frames(seconds: float) -> int:
    n = round((seconds * FPS - 5) / 17)
    return max(124, min(311, 17 * n + 5))  # 311 frames (~13s) is the most this GPU fits in memory


def build(shot_id, refs, seconds, scene, sound, seed):
    pics = {name: i + 1 for i, name in enumerate(refs)}
    defs = [f"<Subject {si}> is " + SUBJECT[n].format(pic=f"<Picture {pics[n]}>") + "."
            for si, n in enumerate([n for n in refs if n in SUBJECT], 1)]
    defs += [f"<Picture {pi}> is {REF_DESC[n]}." for n, pi in pics.items()]
    retention = [f"<Picture {pi}>: fully_preserved - " + RETAIN.get(n, "keep the exact ink-wash drawing style and character design.")
                 for n, pi in pics.items()]
    prompt = (
        "subject_definitions:\n" + "\n".join(defs) + "\n\n"
        "summary:\nA scene from an animated Chinese ink-wash storybook retelling an ancient story. " + STYLE + "\n\n"
        "retention_analysis:\n" + "\n".join(retention) + "\n\n"
        "detailed_description:\n" + scene + CLEAN + " " + STYLE + "\n\n"
        "negative_constraints:\n" + NEGATIVE + "\n\n"
        "overall_soundscape:\n" + sound + " Natural sound effects only.\n\n"
        "non_diegetic_music:\nN/A"
    )
    p = {
        "6": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_ref2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
        "13": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "11": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
        "24": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "121": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["6", 0], "lora_name": "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors", "strength_model": 1.0}},
        "15": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "17": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "9": {"class_type": "BasicScheduler", "inputs": {"model": ["121", 0], "scheduler": "simple", "steps": 4, "denoise": 1.0}},
        "16": {"class_type": "BasicGuider", "inputs": {"model": ["121", 0], "conditioning": ["104", 0]}},
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["15", 0], "guider": ["16", 0], "sampler": ["17", 0], "sigmas": ["9", 0], "latent_image": ["104", 1]}},
        "10": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["14", 0], "vae": ["11", 0], "tile_size": 1344, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}},
        "23": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["14", 0], "vae": ["24", 0]}},
        "91": {"class_type": "CreateVideo", "inputs": {"images": ["10", 0], "audio": ["23", 0], "fps": FPS, "bit_depth": 8}},
        "92": {"class_type": "SaveVideo", "inputs": {"video": ["91", 0], "filename_prefix": f"idiom_{EP}/{shot_id}", "format": "auto", "codec": "auto"}},
        "104": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {
            "clip": ["13", 0], "vae": ["11", 0], "audio_vae": ["24", 0], "prompt": prompt,
            "width": W, "height": H, "length": frames(seconds), "ref_image_size": "match"}},
    }
    for i, name in enumerate(refs):
        node = str(130 + i)
        p[node] = {"class_type": "LoadImage", "inputs": {"image": REF[name]}}
        p["104"]["inputs"][f"ref_images.ref_image_{i}"] = [node, 0]
    return {"prompt": p, "client_id": f"idiom-{EP}-{shot_id}"}


def write(tag=""):
    names = []
    for i, (sid, refs, sec, scene, sound) in enumerate(SHOTS):
        name = f"{sid}_{tag}" if tag else sid
        seed = 660600 + i + (7919 * hash(tag) % 100000 if tag else 0)
        (OUT / f"{name}.api.json").write_text(json.dumps(build(name, refs, sec, scene, sound, seed), ensure_ascii=False, indent=1), encoding="utf-8")
        names.append(name)
    return names


if __name__ == "__main__":
    import sys
    # make_jobs.py            -> all shots
    # make_jobs.py v2 S07 ..  -> re-rolls of the listed shot ids (prefix match), tagged v2
    if len(sys.argv) > 2:
        tag, only = sys.argv[1], sys.argv[2:]
        SHOTS[:] = [s for s in SHOTS if any(s[0].startswith(o) for o in only)]
        names = write(tag)
    else:
        names = write()
    (OUT / "order.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"{len(names)} jobs written")
