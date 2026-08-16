#!/usr/bin/env python3
"""Create a square, word-synchronized Czech Brat-style lyrics MP4."""

import argparse
import asyncio
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
    parser.add_argument("--voice", default="cs-CZ-AntoninNeural")
    parser.add_argument("--rate", default="-8%")
    parser.add_argument("--pitch", default="-2Hz")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--size", type=int, default=1080)
    parser.add_argument("--max-words", type=int, default=6)
    parser.add_argument("--width-ratio", type=float, default=0.74)
    parser.add_argument("--height-ratio", type=float, default=0.68)
    parser.add_argument("--raster-size", type=int, default=360)
    parser.add_argument("--font", type=Path)
    return parser.parse_args()


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


def apply_original_tokens(text, timings):
    original = re.findall(r"\S+", text)
    if len(original) == len(timings):
        for token, timing in zip(original, timings):
            timing["shown"] = token
        return timings
    oi = 0
    for timing in timings:
        target = normalize_token(timing["text"])
        chosen = timing["text"]
        while oi < len(original):
            candidate = original[oi]
            oi += 1
            normalized = normalize_token(candidate)
            if target in normalized or normalized in target:
                chosen = candidate
                break
        timing["shown"] = chosen
    return timings


def build_sets(words, max_words):
    result = []
    start = 0
    for i, word in enumerate(words):
        shown = word["shown"]
        length = i - start + 1
        hard_break = bool(re.search(r"[.!?;:]$", shown))
        comma_break = shown.endswith(",") and length >= 4
        if hard_break or comma_break or length >= max_words:
            result.append((start, i + 1))
            start = i + 1
    if start < len(words):
        result.append((start, len(words)))
    return result


class Renderer:
    def __init__(self, words, sets, font_path, size, width_ratio, height_ratio, raster_size):
        self.words = words
        self.sets = sets
        self.font_path = font_path
        self.size = size
        self.width_ratio = width_ratio
        self.height_ratio = height_ratio
        self.raster_size = raster_size
        self.cache = {}
        self.measure_font = ImageFont.truetype(str(font_path), 100)
        self.measure_draw = ImageDraw.Draw(Image.new("L", (8, 8)))
        self.starts = [words[a]["start"] for a, _ in sets]

    def line_width(self, line):
        box = self.measure_draw.textbbox((0, 0), line, font=self.measure_font)
        return max(1, box[2] - box[0])

    def best_lines(self, tokens):
        max_w = self.size * self.width_ratio
        max_h = self.size * self.height_ratio
        best = None
        for mask in range(1 << max(0, len(tokens) - 1)):
            lines = []
            current = tokens[0]
            for i, token in enumerate(tokens[1:]):
                if mask & (1 << i):
                    lines.append(current)
                    current = token
                else:
                    current += " " + token
            lines.append(current)
            widths = [self.line_width(line) for line in lines]
            size_by_w = 100 * max_w / max(widths)
            size_by_h = 100 * max_h / (104 * len(lines))
            font_size = min(size_by_w, size_by_h, self.size * 0.25)
            normalized = [w / max(widths) for w in widths]
            ragged = sum((1 - x) ** 2 for x in normalized) / len(normalized)
            score = font_size - 10 * ragged
            if best is None or score > best[0]:
                best = (score, lines, int(font_size))
        return best[1], max(34, best[2])

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
        canvas = Image.new("RGB", (self.size, self.size), (255, 255, 255))
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
            ink = Image.new("RGB", text.size, (8, 8, 8))
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

    with tempfile.TemporaryDirectory(prefix="brat-video-") as tmp:
        audio_path = Path(tmp) / "speech.mp3"
        words = asyncio.run(synthesize(text, args.voice, args.rate, args.pitch, audio_path))
        if not words:
            raise SystemExit("TTS returned no word timings")
        words = apply_original_tokens(text, words)
        sets = build_sets(words, args.max_words)
        duration = probe_duration(audio_path)
        renderer = Renderer(words, sets, font_path, args.size, args.width_ratio, args.height_ratio, args.raster_size)
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

    print(json.dumps({
        "output": str(args.output),
        "duration": probe_duration(args.output),
        "size_bytes": args.output.stat().st_size,
        "word_states": len(words) + 1,
        "text_sets": len(sets),
        "voice": args.voice,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
