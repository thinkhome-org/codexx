#!/usr/bin/env python3
"""Offline fallback for Czech Brat-style lyrics videos.

Uses a locally installed Czech TTS engine (macOS say or espeak-ng/espeak),
then derives deterministic source-token timings from the synthesized audio.
"""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError as exc:
    raise SystemExit("Missing Pillow. Install task-locally: pip install --target .brat-video-deps pillow") from exc

COLOR_NAMES = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "brat-green": (138, 206, 0),
    "green": (138, 206, 0),
}

def parse_args():
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text")
    src.add_argument("--text-file", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--voice", default="auto", help="auto, espeak[:voice], say[:voice], or the originally requested voice name")
    p.add_argument("--backend", choices=("auto", "say", "espeak"), default="auto")
    p.add_argument("--rate", default="-8%")
    p.add_argument("--pitch", default="-2Hz")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--size", type=int, default=1080)
    p.add_argument("--max-words", type=int, default=0)
    p.add_argument("--width-ratio", type=float, default=0.74)
    p.add_argument("--height-ratio", type=float, default=0.68)
    p.add_argument("--raster-size", type=int, default=360)
    p.add_argument("--font", type=Path)
    p.add_argument("--background", required=True)
    p.add_argument("--text-color", default="black")
    p.add_argument("--manifest", type=Path)
    return p.parse_args()

def parse_color(value):
    v = value.strip().casefold()
    if v in COLOR_NAMES:
        return COLOR_NAMES[v]
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", value.strip())
    if not m:
        raise SystemExit(f"Unsupported color: {value}")
    h = m.group(1)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def probe_duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())

def find_font(explicit=None):
    if explicit:
        if not explicit.is_file():
            raise SystemExit(f"Font not found: {explicit}")
        return explicit
    candidates = [
        "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Regular.otf",
        "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/System/Library/Fonts/Supplemental/Arial Narrow.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for c in candidates:
        if Path(c).is_file():
            return Path(c)
    raise SystemExit("No narrow sans font found; pass --font")

def rate_to_wpm(rate, base=175):
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)%", str(rate).strip())
    if not m:
        return base
    return max(80, min(350, round(base * (1.0 + float(m.group(1)) / 100.0))))

def list_say_voices():
    if not shutil.which("say"):
        return []
    try:
        out = subprocess.check_output(["say", "-v", "?"], text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return []
    result = []
    for line in out.splitlines():
        m = re.match(r"^(\S.*?)\s{2,}([a-z]{2}_[A-Z]{2})\s+#", line)
        if m:
            result.append((m.group(1).strip(), m.group(2)))
    return result

def choose_say_voice(requested):
    voices = list_say_voices()
    names = [name for name, _ in voices]
    if requested.startswith("say:"):
        wanted = requested.split(":", 1)[1]
        if wanted in names:
            return wanted
        raise SystemExit(f"Requested macOS say voice not installed: {wanted}")
    czech = [name for name, locale in voices if locale == "cs_CZ"]
    lower = requested.casefold()
    preferences = ["Zuzana", "Iveta", "Tomas"] if ("vlasta" in lower or "female" in lower) else ["Tomas", "Zuzana", "Iveta"]
    for name in preferences:
        if name in czech:
            return name
    return czech[0] if czech else None

def choose_backend(args):
    voice = args.voice.strip()
    if voice.startswith("say:"):
        return "say"
    if voice.startswith("espeak:") or voice.casefold() in {"espeak", "espeak-cs", "offline"}:
        return "espeak"
    if args.backend != "auto":
        return args.backend
    if shutil.which("say") and choose_say_voice(voice):
        return "say"
    if shutil.which("espeak-ng") or shutil.which("espeak"):
        return "espeak"
    raise SystemExit("No offline Czech TTS engine found. Install espeak-ng/espeak, or on macOS install a Czech system voice for `say`.")

def synthesize_offline(text, args, workdir):
    backend = choose_backend(args)
    wpm = rate_to_wpm(args.rate)
    if backend == "say":
        voice = choose_say_voice(args.voice)
        if not voice:
            raise SystemExit("No Czech macOS `say` voice is installed")
        path = workdir / "speech.aiff"
        subprocess.run(["say", "-v", voice, "-r", str(wpm), "-o", str(path), text], check=True)
        return path, "say", voice
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise SystemExit("eSpeak is not installed (need espeak-ng or espeak)")
    requested = args.voice.strip()
    voice = requested.split(":", 1)[1] if requested.startswith("espeak:") else "cs"
    path = workdir / "speech.wav"
    subprocess.run([exe, "-v", voice, "-s", str(wpm), "-w", str(path), text], check=True)
    return path, Path(exe).name, voice

def token_weight(token):
    clean = re.sub(r"[^0-9A-Za-zÀ-ž]", "", token)
    w = max(1.0, len(clean) ** 0.62)
    if re.search(r"[.!?…]+[\"'»”)]*$", token):
        w += 2.6
    elif re.search(r"[,;:][\"'»”)]*$", token):
        w += 1.0
    return w

def derive_word_timings(text, duration):
    tokens = re.findall(r"\S+", text)
    weights = [token_weight(t) for t in tokens]
    scale = duration / max(sum(weights), 1e-9)
    words = []
    start = 0.0
    for token, weight in zip(tokens, weights):
        d = weight * scale
        words.append({"text": "", "shown": token, "start": start, "duration": d, "synthetic": True})
        start += d
    return words

def build_sets(words, max_words):
    result = []
    start = 0
    for i, word in enumerate(words):
        shown = word["shown"]
        length = i - start + 1
        hard = bool(re.search(r"[.!?…]+[\"'»”)]*$", shown))
        safe = bool(re.search(r"[,;:][\"'»”)]*$", shown))
        soft = max_words > 0 and length >= max_words and safe
        if hard or soft:
            result.append((start, i + 1))
            start = i + 1
    if start < len(words):
        result.append((start, len(words)))
    return result

def line_width(draw, font, line):
    b = draw.textbbox((0, 0), line, font=font)
    return b[2] - b[0]

def wrap(tokens, font, draw, max_width):
    lines, current = [], []
    for token in tokens:
        candidate = " ".join(current + [token])
        if current and line_width(draw, font, candidate) > max_width:
            lines.append(" ".join(current))
            current = [token]
        else:
            current.append(token)
    if current:
        lines.append(" ".join(current))
    return lines

def fit(tokens, font_path, raster_size, width_ratio, height_ratio):
    probe = Image.new("L", (raster_size, raster_size))
    draw = ImageDraw.Draw(probe)
    max_w = int(raster_size * width_ratio)
    max_h = int(raster_size * height_ratio)
    lo, hi = 7, max(7, int(raster_size * 0.25))
    best = (lo, [" ".join(tokens)])
    while lo <= hi:
        fs = (lo + hi) // 2
        font = ImageFont.truetype(str(font_path), fs)
        lines = wrap(tokens, font, draw, max_w)
        boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
        widths = [b[2] - b[0] for b in boxes]
        heights = [b[3] - b[1] for b in boxes]
        line_h = max(heights, default=fs) + max(1, int(fs * 0.04))
        if max(widths, default=0) <= max_w and line_h * len(lines) <= max_h:
            best = (fs, lines)
            lo = fs + 1
        else:
            hi = fs - 1
    return best

def render_state(tokens, output, font_path, args, background, foreground):
    size = args.raster_size
    fs, lines = fit(tokens, font_path, size, args.width_ratio, args.height_ratio)
    font = ImageFont.truetype(str(font_path), fs)
    image = Image.new("RGB", (size, size), background)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    widths = [b[2] - b[0] for b in boxes]
    heights = [b[3] - b[1] for b in boxes]
    gap = max(1, int(fs * 0.04))
    line_h = max(heights, default=fs) + gap
    block_w = max(widths, default=0)
    block_h = line_h * len(lines) - gap
    x0 = (size - block_w) // 2
    y = (size - block_h) // 2
    for line, box in zip(lines, boxes):
        draw.text((x0 - box[0], y - box[1]), line, font=font, fill=255)
        y += line_h
    bbox = mask.getbbox()
    if bbox:
        layer = mask.crop(bbox)
        layer = layer.resize((max(1, int(layer.width * 1.06)), layer.height), Image.Resampling.BILINEAR)
        layer = layer.filter(ImageFilter.GaussianBlur(0.22))
        ink = Image.new("RGB", layer.size, foreground)
        x = (size - layer.width) // 2
        y = (size - layer.height) // 2
        image.paste(ink, (x, y), layer)
    image.save(output, optimize=True)

def main():
    args = parse_args()
    for exe in ("ffmpeg", "ffprobe"):
        if not shutil.which(exe):
            raise SystemExit(f"Required executable not found: {exe}")
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
    text = " ".join(text.split())
    if not text:
        raise SystemExit("Text is empty")
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    font_path = find_font(args.font)
    background = parse_color(args.background)
    foreground = parse_color(args.text_color)
    with tempfile.TemporaryDirectory(prefix="brat-offline-") as td:
        workdir = Path(td)
        audio_path, backend_used, actual_voice = synthesize_offline(text, args, workdir)
        duration = probe_duration(audio_path)
        words = derive_word_timings(text, duration)
        sets = build_sets(words, args.max_words)
        frames_dir = workdir / "states"
        frames_dir.mkdir()
        concat = workdir / "states.ffconcat"
        set_start_for_word = {}
        for a, b in sets:
            for i in range(a, b):
                set_start_for_word[i] = a
        with concat.open("w", encoding="utf-8") as f:
            f.write("ffconcat version 1.0\n")
            for i, word in enumerate(words):
                state = frames_dir / f"{i:06d}.png"
                a = set_start_for_word[i]
                render_state([w["shown"] for w in words[a:i + 1]], state, font_path, args, background, foreground)
                f.write(f"file '{state.as_posix()}'\n")
                f.write(f"duration {word['duration']:.9f}\n")
            if words:
                last = frames_dir / f"{len(words)-1:06d}.png"
                f.write(f"file '{last.as_posix()}'\n")
        command = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-safe", "0", "-f", "concat", "-i", str(concat), "-i", str(audio_path),
            "-vf", f"scale={args.size}:{args.size}:flags=bilinear,fps={args.fps}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", str(args.output),
        ]
        subprocess.run(command, check=True)
    source_tokens = re.findall(r"\S+", text)
    shown = [w["shown"] for w in words]
    if shown != source_tokens:
        raise SystemExit("Displayed tokens do not exactly equal source tokens")
    manifest = {
        "source_text": text,
        "requested_voice": args.voice,
        "tts_backend": backend_used,
        "actual_voice": actual_voice,
        "timing_mode": "estimated-from-offline-audio",
        "background": args.background,
        "text_color": args.text_color,
        "source_words": len(source_tokens),
        "displayed_words": len(words),
        "synthetic_timings": len(words),
        "words": words,
        "sets": [{"start": a, "end": b, "text": " ".join(w["shown"] for w in words[a:b])} for a, b in sets],
    }
    if args.manifest:
        manifest_path = args.manifest.resolve()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output), "duration": probe_duration(args.output), "size_bytes": args.output.stat().st_size,
        "requested_voice": args.voice, "tts_backend": backend_used, "actual_voice": actual_voice,
        "timing_mode": manifest["timing_mode"], "source_words": manifest["source_words"], "displayed_words": manifest["displayed_words"],
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
