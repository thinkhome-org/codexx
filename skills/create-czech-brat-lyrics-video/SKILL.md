---
name: create-czech-brat-lyrics-video
description: Create square Brat-style Czech lyrics/text videos with selectable neural voice and background, hard word-synchronized dynamic reflow, sentence-safe grouping, guaranteed source-word coverage, generous whitespace, and a soft low-resolution Arial-like texture. Use for Brat lyrics videos, Brat text-generator videos, 1:1 kinetic typography, Czech TTS captions, white or classic Brat-green variants, or videos that must instantly recompute the full layout after every spoken word without transitions.
---

# Create Czech Brat Lyrics Video

Produce a finished MP4 from user-provided text with the bundled generator.

## Ask for creative choices first

If the user has not already specified both choices, pause before rendering and ask one compact question covering:

1. **Voice:** Antonín (`cs-CZ-AntoninNeural`, male), Vlasta (`cs-CZ-VlastaNeural`, female), or a custom Edge TTS voice ID.
2. **Background:** white, classic Brat green (`#8ACE00`), or a custom hex color.

Never silently select Antonín or white. Only choose on the user's behalf when the user explicitly says to choose freely. Default text color to black unless contrast or the user requires otherwise.

## Preserve the format

- Use a 1:1 canvas, 1080 × 1080, 30 fps.
- Preserve natural capitalization, punctuation, and every source token.
- Reveal complete words only.
- At each spoken-word boundary, hard-cut to a newly recomputed layout of the full current sentence.
- Keep a sentence together until `.`, `!`, `?`, or `…`. Never reset merely because a word count was reached.
- Add optional clause splitting only when explicitly needed for an unusually long sentence; split only after a comma, colon, or semicolon.
- Never add fades, tweens, crossfades, motion blur, colored word emphasis, black scenes, or character-by-character typing unless requested.
- Fit a narrow sans-serif block inside roughly 74% of the canvas width and 68% of its height, leaving generous whitespace.
- Center the block, left-align its lines, stretch glyphs slightly, then downsample and upscale the finished frame for the soft low-resolution Brat texture.

## Workflow

1. Use the user's wording verbatim unless they explicitly request proofreading or pair this skill with a rewrite skill.
2. Resolve this skill directory by matching the `name` frontmatter; do not assume its reconciled folder name.
3. Confirm `ffmpeg`, `ffprobe`, and Python are available.
4. Install missing Python dependencies into a task-local directory, never globally:

   ```bash
   python3 -m pip install --target .brat-video-deps edge-tts pillow
   ```

5. Run the bundled generator with an explicit voice, explicit background, and a manifest:

   ```bash
   PYTHONPATH=.brat-video-deps python3 \
     /resolved/skill/path/scripts/create_brat_lyrics_video.py \
     --text "UŽIVATELŮV TEXT" \
     --voice cs-CZ-VlastaNeural \
     --background brat-green \
     --text-color black \
     --manifest /absolute/path/video-manifest.json \
     --output /absolute/path/brat-video.mp4
   ```

6. Adjust delivery only when requested, using `--rate=-8%` and `--pitch=-2Hz` style values.
7. Inspect the manifest before visual QA:
   - require `source_words == displayed_words`;
   - require the ordered `words[].shown` sequence to equal the whitespace-tokenized source exactly;
   - require every normal set to end at sentence punctuation;
   - reject any omitted, duplicated, or reordered token.
8. Inspect a contact sheet and at least one original-resolution frame. Check every sentence-ending state, whitespace, legibility, punctuation, chosen colors, and low-resolution texture.
9. Validate with `ffprobe`: H.264 video, AAC audio, 1080 × 1080, 30 fps, and duration matching the synthesized audio.
10. Save the MP4 persistently and return its download link.

## Generator controls

```bash
--voice cs-CZ-AntoninNeural # Required; never implicit
--voice cs-CZ-VlastaNeural  # Required; never implicit
--background white          # Required
--background brat-green     # Classic #8ACE00
--background '#RRGGBB'      # Custom background
--text-color black          # black, white, or #RRGGBB
--max-words 0               # 0 keeps full sentences; positive values split only at safe clause punctuation
--raster-size 360           # Lower means rougher/softer texture
--width-ratio 0.74          # Smaller means more horizontal whitespace
--height-ratio 0.68         # Smaller means more vertical whitespace
--font /path/font           # Override the detected narrow sans font
```

## Quality gate

Reject and regenerate the output if any of these occur:

- a sentence resets before sentence-ending punctuation without an explicitly requested clause split;
- any source word is missing, duplicated, reordered, spoken but not displayed, or displayed but not represented in the source;
- the selected voice or background differs from the user's choice;
- text animates between layouts instead of changing instantly;
- a partial word or individual character appears;
- only the new word moves while the rest of the block stays fixed;
- text touches the frame edge or feels crowded;
- capitalization or punctuation differs from the supplied text;
- the voice does not pronounce Czech naturally;
- the output lacks either audio or video.
