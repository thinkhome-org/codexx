#!/usr/bin/env python3
"""Create a square, word-synchronized Czech Brat-style lyrics MP4."""

import argparse
import asyncio
import difflib
import json
import math
import os
import re
import shutil
import ssl
import subprocess
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError as exc:
    raise SystemExit("Missing Pillow. Install task-locally: pip install --target .brat-video-deps pillow edge-tts") from exc

try:
    import edge_tts.communicate as edge_communicate
    from edge_tts import Communicate
except ImportError as exc:
    raise SystemExit("Missing edge-tts. Install task-locally: pip install --target .brat-video-deps pillow edge-tts") from exc


def parse_args():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--text-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--rate", default="-8%")
    parser.add_argument("--pitch", default="-2Hz")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--size", type=int, default=1080)
    parser.add_argument(
        "--max-words", type=int, default=0,
        help="Soft clause length. 0 keeps every sentence together; a positive value may split only at clause punctuation.",
    )
    parser.add_argument("--width-ratio", type=float, default=0.74)
    parser.add_argument("--height-ratio", type=float, default=0.68)
    parser.add_argument("--raster-size", type=int, default=360)
    parser.add_argument("--font", type=Path)
    parser.add_argument(
        "--background", required=True,
        help="white, brat-green, black, or a #RRGGBB color",
    )
    parser.add_argument(
        "--text-color", default="black",
        help="black, white, or a #RRGGBB color",
    )
    parser.add_argument("--manifest", type=Path)
    return parser.parse_args()


COLOR_NAMES = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "brat-green": (138, 206, 0),
    "green": (138, 206, 0),
}


def parse_color(value):
    normalized = value.strip().casefold()
    if normalized in COLOR_NAMES:
        return COLOR_NAMES[normalized]
    match = re.fullmatch(r"#?([0-9a-fA-F]{6})", value.strip())
    if not match:
        raise SystemExit(f"Unsupported color {value!r}; use white, black, brat-green, or #RRGGBB")
    hex_color = match.group(1)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


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
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return Path(candidate)
    raise SystemExit("No suitable narrow sans-serif font found; pass --font /absolute/path/font.ttf")


def configure_proxy_ca():
    ca_file = os.getenv("CODEX_PROXY_CERT")
    if ca_file and Path(ca_file).is_file():
        edge_communicate._SSL_CTX = ssl.create_default_context(cafile=ca_file)


async def synthesize(text, voice, rate, pitch, audio_path):
    configure_proxy_ca()
    timings = []
    communication = Communicate(
        text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        boundary="WordBoundary",
    )
    with audio_path.open("wb") as audio:
        async for chunk in communication.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                timings.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,
                    "duration": chunk["duration"] / 10_000_000,
                })
    return timings


def normalize_token(token):
    return re.sub(r"[^0-9A-Za-zÀ-ž]", "", token).casefold()


def token_similarity(original, spoken):
    a = normalize_token(original)
    b = normalize_token(spoken)
    if not a or not b:
        return -2.0
    if a == b:
        return 5.0
    if a in b or b in a:
        return 3.0
    return 3.0 * difflib.SequenceMatcher(None, a, b).ratio() - 2.0


def align_original_tokens(text, timings, audio_duration):
    """Return one timed entry per source token, even when TTS boundaries differ."""
    original = re.findall(r"\S+", text)
    n = len(original)
    m = len(timings)
    gap = -1.0
    score = [[float("-inf")] * (m + 1) for _ in range(n + 1)]
    move = [[None] * (m + 1) for _ in range(n + 1)]
    score[0][0] = 0.0
    for i in range(1, n + 1):
        score[i][0] = score[i - 1][0] + gap
        move[i][0] = "original-gap"
    for j in range(1, m + 1):
        score[0][j] = score[0][j - 1] + gap
        move[0][j] = "timing-gap"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            options = [
                (score[i - 1][j - 1] + token_similarity(original[i - 1], timings[j - 1]["text"]), "match"),
                (score[i - 1][j] + gap, "original-gap"),
                (score[i][j - 1] + gap, "timing-gap"),
            ]
            score[i][j], move[i][j] = max(options, key=lambda item: item[0])

    mapped = {}
    i, j = n, m
    while i or j:
        action = move[i][j]
        if action == "match":
            if token_similarity(original[i - 1], timings[j - 1]["text"]) > 0:
                mapped[i - 1] = j - 1
            i -= 1
            j -= 1
        elif action == "original-gap":
            i -= 1
        elif action == "timing-gap":
            j -= 1
        else:
            break

    known = sorted(mapped)
    result = []
    for index, token in enumerate(original):
        if index in mapped:
            timing = timings[mapped[index]]
            start = timing["start"]
            duration = timing["duration"]
            spoken = timing["text"]
            synthetic = False
        else:
            previous = max((k for k in known if k < index), default=None)
            following = min((k for k in known if k > index), default=None)
            if previous is not None and following is not None:
                left = timings[mapped[previous]]["start"]
                right = timings[mapped[following]]["start"]
                fraction = (index - previous) / (following - previous)
                start = left + (right - left) * fraction
            elif following is not None:
                right = timings[mapped[following]]["start"]
                start = right * (index + 1) / (following + 1)
            elif previous is not None:
                left_timing = timings[mapped[previous]]
                left = left_timing["start"] + left_timing["duration"]
                remaining = max(0.0, audio_duration - left)
                fraction = (index - previous) / max(1, n - previous)
                start = left + remaining * fraction
            else:
                start = audio_duration * index / max(1, n)
            duration = 0.05
            spoken = ""
            synthetic = True
        result.append({
            "text": spoken,
            "shown": token,
            "start": max(0.0, min(start, audio_duration)),
            "duration": max(0.01, duration),
            "synthetic": synthetic,
        })

    for index in range(1, len(result)):
        result[index]["start"] = max(result[index]["start"], result[index - 1]["start"])
    shown = [word["shown"] for word in result]
    if shown != original:
        raise SystemExit("Internal word coverage error: displayed tokens do not exactly match the source text")
    return result


def build_sets(words, max_words):
    result = []
    start = 0
    for i, word in enumerate(words):
        shown = word["shown"]
        length = i - start + 1
        hard_break = bool(re.search(r"[.!?…]+[\"'»”)]*$", shown))
        safe_clause_break = bool(re.search(r"[,;:][\"'»”)]*$", shown))
        soft_break = max_words > 0 and length >= max_words and safe_clause_break
        if hard_break or soft_break:
            result.append((start, i + 1))
            start = i + 1
    if start < len(words):
        result.append((start, len(words)))
    return result


class Renderer:
    def __init__(self, words, sets, font_path, size, width_ratio, height_ratio, raster_size, background, foreground):
        self.words = words
        self.sets = sets
        self.font_path = font_path
        self.size = size
        self.width_ratio = width_ratio
        self.height_ratio = height_ratio
        self.raster_size = raster_size
        self.background = background
        self.foreground = foreground
        self.cache = {}
        self.measure_font = ImageFont.truetype(str(font_path), 100)
        self.measure_draw = ImageDraw.Draw(Image.new("L", (8, 8)))
        self.starts = [words[a]["start"] for a, _ in sets]

    def line_width(self, line):
        box = self.measure_draw.textbbox((0, 0), line, font=self.measure_font)
        return max(1, box[2] - box[0])

    def wrap_lines(self, tokens, font_size):
        max_width_at_100 = self.size * self.width_ratio * 100 / font_size
        n = len(tokens)
        space = self.line_width(" ")
        widths = [self.line_width(token) for token in tokens]
        cost = [float("inf")] * (n + 1)
        choice = [None] * (n + 1)
        cost[n] = 0.0
        for i in range(n - 1, -1, -1):
            line_width = 0.0
            for j in range(i, n):
                line_width += widths[j] + (space if j > i else 0)
                if line_width > max_width_at_100 and j > i:
                    break
                overflow = max(0.0, line_width - max_width_at_100)
                if overflow and j == i:
                    penalty = 1000.0 * (overflow / max_width_at_100) ** 2
                else:
                    slack = max(0.0, max_width_at_100 - line_width) / max_width_at_100
                    penalty = (0.15 if j == n - 1 else 1.0) * slack ** 2
                candidate = penalty + cost[j + 1]
                if candidate < cost[i]:
                    cost[i] = candidate
                    choice[i] = j + 1
        lines = []
        i = 0
        while i < n:
            j = choice[i] or i + 1
            lines.append(" ".join(tokens[i:j]))
            i = j
        return lines

    def best_lines(self, tokens):
        max_h = self.size * self.height_ratio
        low = 14
        high = max(low, int(self.size * 0.25))
        best = (self.wrap_lines(tokens, low), low)
        while low <= high:
            font_size = (low + high) // 2
            lines = self.wrap_lines(tokens, font_size)
            line_height = font_size * 1.08
            fits_height = line_height * len(lines) <= max_h
            fits_width = all(self.line_width(line) * font_size / 100 <= self.size * self.width_ratio for line in lines)
            if fits_height and fits_width:
                best = (lines, font_size)
                low = font_size + 1
            else:
                high = font_size - 1
        return best

    def tokens_at(self, t, duration):
        ends = self.starts[1:] + [duration]
        active = None
        for index, (start, end) in enumerate(zip(self.starts, ends)):
            if start <= t < end:
                active = index
                break
        if active is None:
            return []
        a, b = self.sets[active]
        return [self.words[i]["shown"] for i in range(a, b) if self.words[i]["start"] <= t]

    def frame(self, tokens):
        key = tuple(tokens)
        if key in self.cache:
            return self.cache[key]
        canvas = Image.new("RGB", (self.size, self.size), self.background)
        if not tokens:
            self.cache[key] = canvas
            return canvas
        lines, font_size = self.best_lines(tokens)
        font = ImageFont.truetype(str(self.font_path), font_size)
        gap = max(2, int(font_size * 0.02))
        boxes = [font.getbbox(line) for line in lines]
        widths = [box[2] - box[0] for box in boxes]
        heights = [box[3] - box[1] for box in boxes]
        line_height = max(heights) + gap
        block_w = max(widths)
        block_h = line_height * len(lines) - gap
        x0 = int((self.size - block_w) / 2)
        y0 = int((self.size - block_h) / 2)
        mask = Image.new("L", (self.size, self.size), 0)
        draw = ImageDraw.Draw(mask)
        for i, (line, box) in enumerate(zip(lines, boxes)):
            draw.text((x0 - box[0], y0 + i * line_height - box[1]), line, font=font, fill=255)
        crop = mask.getbbox()
        if crop:
            text = mask.crop(crop)
            text = text.resize((max(1, int(text.width * 1.06)), text.height), Image.Resampling.BILINEAR)
            text = text.filter(ImageFilter.GaussianBlur(0.7))
            x = (self.size - text.width) // 2
            y = (self.size - text.height) // 2
            ink = Image.new("RGB", text.size, self.foreground)
            canvas.paste(ink, (x, y), text)
        canvas = canvas.resize((self.raster_size, self.raster_size), Image.Resampling.BILINEAR)
        canvas = canvas.resize((self.size, self.size), Image.Resampling.BILINEAR)
        self.cache[key] = canvas
        return canvas


def main():
    args = parse_args()
    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise SystemExit(f"Required executable not found: {executable}")
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
    text = " ".join(text.split())
    if not text:
        raise SystemExit("Text is empty")
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    font_path = find_font(args.font)
    background = parse_color(args.background)
    foreground = parse_color(args.text_color)

    with tempfile.TemporaryDirectory(prefix="brat-video-") as tmp:
        audio_path = Path(tmp) / "speech.mp3"
        words = asyncio.run(synthesize(text, args.voice, args.rate, args.pitch, audio_path))
        if not words:
            raise SystemExit("TTS returned no word timings")
        duration = probe_duration(audio_path)
        words = align_original_tokens(text, words, duration)
        sets = build_sets(words, args.max_words)
        renderer = Renderer(
            words, sets, font_path, args.size, args.width_ratio, args.height_ratio,
            args.raster_size, background, foreground,
        )
        frames = math.ceil(duration * args.fps)
        command = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{args.size}x{args.size}",
            "-r", str(args.fps), "-i", "-", "-i", str(audio_path),
            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest",
            str(args.output),
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        try:
            for frame_index in range(frames):
                t = frame_index / args.fps
                process.stdin.write(renderer.frame(renderer.tokens_at(t, duration)).tobytes())
        finally:
            process.stdin.close()
        if process.wait() != 0:
            raise SystemExit("ffmpeg encoding failed")

    manifest = {
        "source_text": text,
        "voice": args.voice,
        "background": args.background,
        "text_color": args.text_color,
        "source_words": len(re.findall(r"\S+", text)),
        "displayed_words": len(words),
        "synthetic_timings": sum(1 for word in words if word["synthetic"]),
        "words": words,
        "sets": [
            {"start": start, "end": end, "text": " ".join(word["shown"] for word in words[start:end])}
            for start, end in sets
        ],
    }
    if args.manifest:
        args.manifest = args.manifest.resolve()
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "output": str(args.output),
        "duration": probe_duration(args.output),
        "size_bytes": args.output.stat().st_size,
        "word_states": len(words) + 1,
        "text_sets": len(sets),
        "voice": args.voice,
        "background": args.background,
        "source_words": manifest["source_words"],
        "displayed_words": manifest["displayed_words"],
        "synthetic_timings": manifest["synthetic_timings"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
