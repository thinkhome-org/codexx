---
name: create-czech-brat-lyrics-video
description: Create square Brat-style Czech lyrics/text videos with selectable Czech TTS, hard word-synchronized dynamic reflow, sentence-safe grouping, guaranteed source-word coverage, generous whitespace, and a soft low-resolution Arial-like texture. Prefer Edge neural voices, but fall back to local macOS Czech voices or eSpeak when online TTS is unavailable.
---

# Create Czech Brat Lyrics Video

Produce a finished MP4 from user-provided text with the bundled generators. Do not fail merely because Edge TTS or network access is unavailable when a local Czech TTS backend can render the video.

## Ask for creative choices first

If the user has not already specified both choices, pause before rendering and ask one compact question covering:

1. **Voice:**
   - Vlasta (`cs-CZ-VlastaNeural`, female Edge neural; preferred when available),
   - Antonín (`cs-CZ-AntoninNeural`, male Edge neural; preferred when available),
   - a custom Edge TTS voice ID,
   - `offline female` / macOS Czech female voice when available,
   - `offline male` / macOS Czech male voice when available,
   - `espeak` / `espeak:cs` for the portable Czech offline fallback.
2. **Background:** white, classic Brat green (`#8ACE00`), or a custom hex color.

Never silently select Antonín or white. Only choose on the user's behalf when the user explicitly says to choose freely. Default text color to black unless contrast or the user requires otherwise.

If the user explicitly selected Vlasta or Antonín and that exact Edge voice cannot be reached, preserve their requested gender where possible: on macOS prefer a Czech system voice of the corresponding gender, otherwise fall back to Czech eSpeak. State the actual backend/voice in the final result; never pretend the fallback is the neural voice.

## TTS backend priority and fallback contract

Use this order unless the user explicitly requests a specific offline backend:

1. **Edge TTS neural** — `cs-CZ-VlastaNeural`, `cs-CZ-AntoninNeural`, or the supplied Edge voice ID. This is the preferred path because it supplies real word boundaries.
2. **macOS `say`** — if running on macOS and a Czech system voice is installed. Prefer `Zuzana`/`Iveta` for a requested female voice and `Tomas` for a requested male voice when present.
3. **eSpeak NG / eSpeak** — use Czech `cs`; portable offline last resort.

A network failure, TLS failure, Edge service failure, missing `edge-tts`, or inability to install it is not by itself a reason to stop. Try the next locally available backend.

The online generator is:

`/resolved/skill/path/scripts/create_brat_lyrics_video.py`

The offline fallback generator is:

`/resolved/skill/path/scripts/create_brat_lyrics_video_offline.py`

Offline TTS engines generally do not expose Edge-style WordBoundary events. The fallback generator therefore derives deterministic source-token timings from the final synthesized audio. Mark this honestly in the manifest as `timing_mode: estimated-from-offline-audio`. Exact source-token coverage remains mandatory even when acoustic word timing is estimated.

## Preserve the format

- Use a 1:1 canvas, 1080 × 1080, 30 fps.
- Preserve natural capitalization, punctuation, and every source token.
- Reveal complete words only.
- At each spoken-word boundary or estimated offline word boundary, hard-cut to a newly recomputed layout of the full current sentence.
- Keep a sentence together until `.`, `!`, `?`, or `…`. Never reset merely because a word count was reached.
- Add optional clause splitting only when explicitly needed for an unusually long sentence; split only after a comma, colon, or semicolon.
- Never add fades, tweens, crossfades, motion blur, colored word emphasis, black scenes, or character-by-character typing unless requested.
- Fit a narrow sans-serif block inside roughly 74% of the canvas width and 68% of its height, leaving generous whitespace.
- Center the block, left-align its lines, stretch glyphs slightly, then downsample and upscale the finished frame for the soft low-resolution Brat texture.

## Workflow

1. Use the user's wording verbatim unless they explicitly request proofreading or pair this skill with a rewrite skill.
2. Resolve this skill directory by matching the `name` frontmatter; do not assume its reconciled folder name.
3. Confirm `ffmpeg`, `ffprobe`, Python, and available TTS backends (`say`, `espeak-ng`, `espeak`).
4. Prefer task-local dependencies for the neural path:

   ```bash
   python3 -m pip install --target .brat-video-deps edge-tts pillow
   ```

   If network/package installation fails, continue to the offline path if Pillow and a supported local TTS engine are already available.

5. Preferred Edge render:

   ```bash
   PYTHONPATH=.brat-video-deps python3 \
     /resolved/skill/path/scripts/create_brat_lyrics_video.py \
     --text "UŽIVATELŮV TEXT" \
     --voice cs-CZ-VlastaNeural \
     --background white \
     --text-color black \
     --manifest /absolute/path/video-manifest.json \
     --output /absolute/path/brat-video.mp4
   ```

6. If the Edge path fails for network/service/dependency reasons, render offline instead of stopping:

   ```bash
   PYTHONPATH=.brat-video-deps python3 \
     /resolved/skill/path/scripts/create_brat_lyrics_video_offline.py \
     --text "UŽIVATELŮV TEXT" \
     --voice espeak:cs \
     --background white \
     --text-color black \
     --manifest /absolute/path/video-manifest.json \
     --output /absolute/path/brat-video.mp4
   ```

   For automatic local selection, pass the originally requested voice name/ID and leave `--backend auto`; the script prefers an installed Czech macOS `say` voice and otherwise eSpeak.

7. Adjust delivery only when requested, using `--rate=-8%` and `--pitch=-2Hz` style values. The offline generator maps percentage rate to an approximate local-engine speaking rate; pitch support depends on the backend.
8. Inspect the manifest before visual QA:
   - require `source_words == displayed_words`;
   - require the ordered `words[].shown` sequence to equal the whitespace-tokenized source exactly;
   - require every normal set to end at sentence punctuation;
   - reject any omitted, duplicated, or reordered token;
   - record `tts_backend`, `actual_voice`, and `timing_mode` for offline renders.
9. Inspect a contact sheet and at least one original-resolution frame. Check every sentence-ending state, whitespace, legibility, punctuation, chosen colors, and low-resolution texture.
10. Validate with `ffprobe`: H.264 video, AAC audio, 1080 × 1080, 30 fps, and duration matching the synthesized audio.
11. Save the MP4 persistently and return its download link.

## Generator controls

```bash
# Preferred neural voices
--voice cs-CZ-AntoninNeural
--voice cs-CZ-VlastaNeural
--voice <custom Edge TTS voice ID>

# Offline fallback examples
--voice espeak:cs
--voice offline
--voice say:Zuzana
--voice say:Tomas
--backend auto
--backend say
--backend espeak

# Video controls
--background white
--background brat-green
--background '#RRGGBB'
--text-color black
--max-words 0
--raster-size 360
--width-ratio 0.74
--height-ratio 0.68
--font /path/font
```

## Quality gate

Reject and regenerate the output if any of these occur:

- a sentence resets before sentence-ending punctuation without an explicitly requested clause split;
- any source word is missing, duplicated, reordered, spoken but not displayed, or displayed but not represented in the source;
- the selected background differs from the user's choice;
- an Edge voice is claimed even though an offline fallback actually rendered the audio;
- the actual TTS backend/voice is omitted from reporting after a fallback;
- text animates between layouts instead of changing instantly;
- a partial word or individual character appears;
- only the new word moves while the rest of the block stays fixed;
- text touches the frame edge or feels crowded;
- capitalization or punctuation differs from the supplied text;
- the chosen engine does not use a Czech voice/language;
- the output lacks either audio or video.

Do not reject a technically valid offline render solely because estimated offline word timings are less acoustically precise than Edge WordBoundary timings. Distinguish exact token coverage from acoustic timing precision and report that distinction clearly.
