---
name: create-czech-brat-lyrics-video
description: Create square Brat-style Czech lyrics/text videos with selectable Czech TTS, hard word-synchronized dynamic reflow, sentence-safe grouping, guaranteed source-word coverage, generous whitespace, and a soft low-resolution Arial-like texture. Preserve the user's full voice choice set even in Codex Online Sessions; prefer Edge neural voices, but use local Czech fallbacks only as a technical render fallback when online TTS is unavailable.
---

# Create Czech Brat Lyrics Video

Produce a finished MP4 from user-provided text with the bundled generators. Do not fail merely because Edge TTS or network access is unavailable when a local Czech TTS backend can render the video.

## Voice selection is always preserved

The voice picker and the render backend are two different things.

Always keep the user's normal voice choices available, including in Codex Online Sessions:

- Vlasta (`cs-CZ-VlastaNeural`)
- Antonín (`cs-CZ-AntoninNeural`)
- custom Edge TTS voice ID
- offline female
- offline male
- `espeak` / `espeak:cs`
- `say:<voice>` when macOS local voices are relevant

Do not remove Vlasta, Antonín, or custom Edge voices merely because the current runtime might not have network access. Do not collapse the UI into a single `espeak` option. The user chooses the desired voice first; backend fallback is handled only during rendering.

If the user selected Vlasta or Antonín, that remains the **requested voice** even if the actual runtime must use an offline Czech fallback. Report both `requested_voice` and `actual_voice`/`tts_backend` separately. Never silently reinterpret `Vlasta` as `espeak` at selection time.

## Ask for creative choices first

If the user has not already specified both choices, pause before rendering and ask one compact question covering:

1. **Voice:**
   - Vlasta (`cs-CZ-VlastaNeural`, female Edge neural),
   - Antonín (`cs-CZ-AntoninNeural`, male Edge neural),
   - a custom Edge TTS voice ID,
   - `offline female`,
   - `offline male`,
   - `espeak` / `espeak:cs`,
   - `say:<voice>` on macOS.
2. **Background:** white, classic Brat green (`#8ACE00`), or a custom hex color.

Never silently select Antonín or white. Only choose on the user's behalf when the user explicitly says to choose freely. Default text color to black unless contrast or the user requires otherwise.

## TTS backend priority and Codex Online behavior

After the user has chosen a voice, render using this order unless a specific offline backend was explicitly requested:

1. **Edge TTS neural** — use the exact requested Edge voice (`cs-CZ-VlastaNeural`, `cs-CZ-AntoninNeural`, or custom ID). This remains the preferred path and provides real WordBoundary timing.
2. **macOS `say`** — only when locally available. For a requested female voice prefer Czech Zuzana/Iveta; for male prefer Tomas when installed.
3. **eSpeak NG / eSpeak** — use Czech `cs` as the portable offline fallback.

In Codex Online Sessions, assume that outbound network/package installation may be unavailable. That must not change the available voice choices. Attempt the requested Edge path when possible; if it fails for network, TLS, service, or dependency reasons, continue with a local Czech fallback if one exists.

A network failure, TLS failure, Edge service failure, missing `edge-tts`, or inability to install it is not by itself a reason to stop the video task.

If no usable Czech TTS backend exists at all, state that rendering cannot complete in that runtime. Do not pretend a non-Czech or nonexistent voice succeeded.

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
3. Preserve the selected voice exactly as `requested_voice` before probing backend availability.
4. Confirm `ffmpeg`, `ffprobe`, Python, and available TTS backends (`say`, `espeak-ng`, `espeak`).
5. Prefer task-local dependencies for the neural path:

   ```bash
   python3 -m pip install --target .brat-video-deps edge-tts pillow
   ```

   If network/package installation fails, continue to the offline path if Pillow and a supported local TTS engine are already available.

6. Preferred Edge render:

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

7. If the Edge path fails for network/service/dependency reasons, render offline instead of stopping:

   ```bash
   PYTHONPATH=.brat-video-deps python3 \
     /resolved/skill/path/scripts/create_brat_lyrics_video_offline.py \
     --text "UŽIVATELŮV TEXT" \
     --voice "Vlasta" \
     --backend auto \
     --background white \
     --text-color black \
     --manifest /absolute/path/video-manifest.json \
     --output /absolute/path/brat-video.mp4
   ```

   Pass the originally selected semantic voice name/ID into the offline generator. Let `--backend auto` choose the best locally available Czech fallback while preserving the requested voice separately in the manifest.

8. Adjust delivery only when requested, using `--rate=-8%` and `--pitch=-2Hz` style values. The offline generator maps percentage rate to an approximate local-engine speaking rate; pitch support depends on the backend.
9. Inspect the manifest before visual QA:
   - require `source_words == displayed_words`;
   - require the ordered `words[].shown` sequence to equal the whitespace-tokenized source exactly;
   - require every normal set to end at sentence punctuation;
   - reject any omitted, duplicated, or reordered token;
   - record `requested_voice`, `tts_backend`, `actual_voice`, and `timing_mode` for fallback renders.
10. Inspect a contact sheet and at least one original-resolution frame. Check every sentence-ending state, whitespace, legibility, punctuation, chosen colors, and low-resolution texture.
11. Validate with `ffprobe`: H.264 video, AAC audio, 1080 × 1080, 30 fps, and duration matching the synthesized audio.
12. Save the MP4 persistently and return its download link.

## Generator controls

```bash
# Normal selectable voices — keep these choices available regardless of runtime
--voice cs-CZ-AntoninNeural
--voice cs-CZ-VlastaNeural
--voice <custom Edge TTS voice ID>

# Explicit offline choices
--voice offline
--voice espeak:cs
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

- the normal voice choices were hidden or removed merely because the runtime is Codex Online or offline;
- `requested_voice` was silently changed to the fallback backend name;
- a sentence resets before sentence-ending punctuation without an explicitly requested clause split;
- any source word is missing, duplicated, reordered, spoken but not displayed, or displayed but not represented in the source;
- the selected background differs from the user's choice;
- an Edge voice is claimed as the actual rendered voice when an offline fallback rendered the audio;
- the actual TTS backend/voice is omitted from reporting after a fallback;
- text animates between layouts instead of changing instantly;
- a partial word or individual character appears;
- only the new word moves while the rest of the block stays fixed;
- text touches the frame edge or feels crowded;
- capitalization or punctuation differs from the supplied text;
- the chosen engine does not use a Czech voice/language;
- the output lacks either audio or video.

Do not reject a technically valid offline render solely because estimated offline word timings are less acoustically precise than Edge WordBoundary timings. Distinguish exact token coverage from acoustic timing precision and report that distinction clearly.
