"""Server-side replacement for moss_client.py: speak lines with MOSS-TTS directly on the GPU server.

Same interface as moss_client.synth(items, job), so an episode's build.py can switch with one import:
  items = [(mp3_path, voice_name, text, language, tempo)]
- voice_name: /root/autodl-tmp/moss/voices_idiom/<name>.wav (the fixed channel voices)
- tempo: ffmpeg atempo factor; leading/trailing silence is trimmed; writes an empty "<name>.json" (proportional captions)
Existing mp3 files are skipped, so delete one (and its server wav) to re-roll a line.
ComfyUI must have released its VRAM first (POST /free), MOSS 8B needs ~17 GB.
"""

import json
import subprocess
from pathlib import Path

MOSS = Path("/root/autodl-tmp/moss")
VOICES = MOSS / "voices_idiom"


def synth(items, job="idiom_tts"):
    todo = [it for it in items if not Path(it[0]).exists()]
    if not todo:
        return
    remote = MOSS / "jobs" / job
    (remote / "out").mkdir(parents=True, exist_ok=True)
    lines = [{"id": Path(p).stem, "ref": str(VOICES / f"{v}.wav"), "text": t, "language": lang}
             for p, v, t, lang, _ in todo if not (remote / "out" / f"{Path(p).stem}.wav").exists()]
    if lines:
        spec = remote / "lines.json"
        spec.write_text(json.dumps(lines, ensure_ascii=False, indent=1), encoding="utf-8")
        env = {"HF_HOME": "/root/autodl-tmp/hf_cache", "HF_HUB_OFFLINE": "1", "PATH": "/usr/bin:/bin"}
        subprocess.run([str(MOSS / "env/bin/python"), "tts_moss.py", "speak", str(spec), str(remote / "out")],
                       cwd=MOSS, env=env, check=True)
    for p, v, t, lang, tempo in todo:
        wav = remote / "out" / f"{Path(p).stem}.wav"
        af = f"atempo={tempo:.3f}," if abs(tempo - 1) > 1e-3 else ""
        af += ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
               "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", af, "-ar", "24000", "-b:a", "96k", str(p)], check=True)
        Path(p).with_suffix(".json").write_text("[]", encoding="utf-8")
