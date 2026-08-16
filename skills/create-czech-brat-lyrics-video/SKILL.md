---
name: create-czech-brat-lyrics-video
description: Create square Brat-style lyrics/text videos with Czech neural text-to-speech, hard word-synchronized dynamic reflow, generous whitespace, and a soft low-resolution Arial-like look. Use when the user requests a Brat lyrics video, Brat text-generator video, 1:1 kinetic typography, Czech TTS captions, or asks to reproduce the specific white-background layout that recomputes instantly after every spoken word without transitions.
---

# Create Czech Brat Lyrics Video

Produce a finished MP4 from user-provided text with the bundled generator.

## Preserve these defaults

- Use a 1:1 canvas, 1080 × 1080, 30 fps.
- Keep the background white and the text black.
- Preserve natural capitalization and punctuation from the input.
- Use Czech neural TTS; default to the male `cs-CZ-AntoninNeural` voice.
- Reveal complete words only. At each spoken-word boundary, hard-cut to a newly recomputed layout of the entire current text set.
- Never add fades, tweens, crossfades, motion blur, colored emphasis, black scenes, or character-by-character typing unless explicitly requested.
- Fit a narrow sans-serif block inside roughly 74% of the canvas width and 68% of its height, leaving generous whitespace.
- Center the block, left-align its lines, stretch glyphs slightly, then downsample and upscale the finished frame for a soft low-resolution Brat texture.

## Workflow

1. Use the user's wording verbatim unless they explicitly request proofreading. Do not silently rewrite dark, poetic, or unusual phrasing.
2. Confirm `ffmpeg`, `ffprobe`, and Python are available.
3. Install missing Python dependencies into a task-local directory, never globally:

   ```bash
   python3 -m pip install --target .brat-video-deps edge-tts pillow
   ```

4. Run the bundled script with that directory on `PYTHONPATH`:

   ```bash
   PYTHONPATH=.brat-video-deps python3 \
     /root/.codex/skills/remote-skills/create-czech-brat-lyrics-video/scripts/create_brat_lyrics_video.py \
     --text "UŽIVATELŮV TEXT" \
     --output /absolute/path/brat-video.mp4
   ```

   After installation reconciliation, resolve the skill directory by matching the `name` frontmatter if the literal path above has changed.

5. For a female Czech voice, pass `--voice cs-CZ-VlastaNeural`. Adjust delivery only when requested, using `--rate=-8%` style values.
6. Inspect a contact sheet and at least one original-resolution frame. Verify whitespace, legibility, punctuation, and the low-resolution texture.
7. Validate the encoded file with `ffprobe`: H.264 video, AAC audio, 1080 × 1080, 30 fps, and duration matching the synthesized audio.
8. Save the user-facing MP4 persistently and return its download link.

## Generator behavior

The script automatically:

- obtains word-boundary timings from Czech TTS;
- groups text at sentence punctuation, commas, and a configurable maximum word count;
- recomputes optimal line breaks and font size after every complete word;
- keeps each typographic state perfectly static until the next word;
- renders a slightly stretched narrow sans-serif face;
- rasterizes at reduced resolution and enlarges it to create the Brat softness;
- muxes the voice into an H.264/AAC MP4.

Useful controls:

```bash
--max-words 6       # Maximum words in one accumulating text set
--raster-size 360   # Lower means rougher/softer low-res texture
--width-ratio 0.74  # Smaller means more horizontal whitespace
--height-ratio 0.68 # Smaller means more vertical whitespace
--font /path/font   # Override the auto-detected narrow sans font
```

## Quality gate

Reject and regenerate the output if any of these occur:

- any black or colored background appears;
- text animates between layouts instead of changing instantly;
- a partial word or individual character appears;
- only the new word moves while the rest of the block stays fixed;
- text touches the frame edge or feels crowded;
- capitalization or punctuation differs from the supplied text;
- the voice does not pronounce Czech naturally;
- the output lacks either audio or video.
