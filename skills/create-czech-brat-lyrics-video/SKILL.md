---
name: create-czech-brat-lyrics-video
description: Create square Brat-style Czech lyrics/text videos with selectable Czech TTS, explicit environment-aware voice choices, selectable text grouping, guaranteed source-word coverage, generous whitespace, and a soft low-resolution Arial-like texture. Prefer Edge neural voices when reachable, but preserve the user's voice choice and fall back to local Czech TTS when required.
---

# Create Czech Brat Lyrics Video

Produce a finished MP4 from user-provided text with the bundled generators. Keep **creative choice** separate from **runtime capability**: the user chooses the voice and grouping style first; only then determine which backend can actually render it in the current environment.

## Ask for all creative choices together

If the user has not already specified them, ask one compact question covering:

1. **Voice**
2. **Background**
3. **Text grouping / when the current text block resets**

Do not silently remove voice options merely because the current runtime may not support one backend. Explain compatibility briefly and let the user choose.

### Voice choices

Offer these choices:

- **Vlasta** — `cs-CZ-VlastaNeural`, female Edge neural. Best natural Czech quality among the built-in named choices when Edge TTS is reachable.
- **Antonín** — `cs-CZ-AntoninNeural`, male Edge neural. Same Edge requirements as Vlasta.
- **Custom Edge voice** — any valid Edge TTS voice ID.
- **Offline female** — local Czech female voice where available; on macOS prefer Zuzana/Iveta.
- **Offline male** — local Czech male voice where available; on macOS prefer Tomas.
- **eSpeak Czech** — `espeak` / `espeak:cs`; portable, fully offline fallback, lower voice quality.
- **Specific macOS voice** — `say:<voice>` when running on macOS with that voice installed.

### Environment compatibility guidance

When presenting the voice menu, include concise guidance like this. Treat it as capability guidance, not a guarantee; Codex runtimes can change.

| Voice/backend | ChatGPT/Codex with outbound network | Codex Online Session with restricted network | Local macOS Codex | Linux/offline server | Quality | Reliability |
|---|---|---|---|---|---|---|
| Vlasta / Antonín via Edge | Usually best choice when Edge is reachable | May fail if outbound Edge TTS or package install is blocked | Usually works if network is allowed | Works only with network | High | Medium, network-dependent |
| Custom Edge voice | Same as Edge named voices | Same restrictions | Same restrictions | Same restrictions | High | Medium, network-dependent |
| macOS `say` Czech | Only on macOS | Usually unavailable in Linux-based online sessions | Very likely if Czech system voice is installed | Unavailable | Medium to high depending on installed voice | High on configured macOS |
| eSpeak NG / eSpeak Czech | Works if binary exists | **Highest-probability offline fallback in Linux-style Codex sessions when installed** | Works if installed | Very likely on configured Linux | Low/robotic | High, no network |

For **Codex Online Sessions**, recommend this practical order:

1. Choose **Vlasta or Antonín** if voice quality matters; try Edge first.
2. If the session cannot reach Edge TTS, use the chosen voice as the *requested voice* but render through an available fallback.
3. In Linux-style restricted sessions, **eSpeak Czech is usually the safest offline option when installed**.
4. macOS `say` is relevant only to macOS runtimes, not generic hosted Linux sessions.

Never claim that a specific backend is guaranteed to exist until you inspect the runtime.

### Voice-choice preservation contract

The selected voice is a creative preference; the TTS backend is an implementation detail.

If the user chooses Vlasta, Antonín, or a custom Edge voice:

1. keep that as `requested_voice`;
2. try the exact Edge voice first;
3. if Edge cannot run because of network, TLS, service availability, dependency installation, or runtime restrictions, use a compatible Czech local backend if one exists;
4. preserve requested gender when possible;
5. report `requested_voice`, `tts_backend`, and `actual_voice` separately.

Never change the user's visible voice menu based solely on runtime detection. Never pretend an offline fallback is actually Vlasta or Antonín.

## Background choices

- `white`
- `brat-green` (`#8ACE00`)
- custom `#RRGGBB`

Default text color to black unless contrast or the user requires otherwise.

## Text grouping choices

The user must be able to choose **when the accumulating Brat text block resets**. Offer these modes:

### 1. `legacy` — recommended default

Reproduces the original shorter-block behavior from the first generator version.

- Reset at `.`, `!`, `?`, `;`, or `:`.
- Reset at a comma once the block has at least about four words.
- Otherwise reset after a hard word limit.
- Default hard limit: **6 words**.
- User may customize the limit with `--max-words N`.

Use:

- online: `create_brat_lyrics_video_legacy.py`
- offline: `create_brat_lyrics_video_offline_legacy.py`

**Recommend `legacy` by default** because it keeps text large, fast, and visually close to the original Brat-style implementation.

### 2. `sentence`

Current full-sentence behavior.

- Keep accumulating until `.`, `!`, `?`, or `…`.
- Do not reset merely because the sentence is long.
- Best for preserving complete grammatical units.
- Can produce much smaller text on long baroque sentences.

Use the normal generator with `--max-words 0`.

### 3. `clause`

Compromise between legacy and sentence modes.

- Always reset at sentence-ending punctuation.
- For long blocks, permit reset only at a safe comma, semicolon, or colon after the configured soft threshold.
- Recommended soft threshold: **8–12 words**; use 10 unless the user chooses another value.

Use the normal generator with `--max-words N` where `N > 0`.

### 4. Custom grouping

If the user wants exact behavior, let them specify:

- mode: `legacy`, `sentence`, or `clause`;
- `max words` / threshold;
- whether comma, semicolon, and colon may reset the block.

Do not invent a custom policy when the user already supplied one.

### Grouping recommendation shown to users

When asking, summarize the tradeoff:

- **Legacy (recommended):** largest text, fastest changes, original feel.
- **Sentence:** complete sentences, calmer structure, can shrink heavily on long sentences.
- **Clause:** balanced middle option; readable without arbitrary mid-phrase cuts.

If the user does not choose a grouping mode and has not explicitly asked to leave it to you, use **`legacy` with 6 words** as the default and state that default before rendering. Unlike voice/background, grouping has an explicit recommended default because it is a technical presentation behavior rather than an identity-like creative voice choice.

## TTS backend priority and fallback

Unless the user explicitly requests a specific offline backend:

1. Edge TTS neural.
2. macOS `say` when on macOS with a Czech voice.
3. eSpeak NG / eSpeak Czech.

A network failure, TLS failure, Edge service failure, missing `edge-tts`, or inability to install it is not by itself a reason to stop if another Czech backend can render.

## Generator mapping

### Sentence / clause, Edge

`/resolved/skill/path/scripts/create_brat_lyrics_video.py`

- sentence: `--max-words 0`
- clause: `--max-words 10` by default, or the user-selected threshold

### Legacy, Edge

`/resolved/skill/path/scripts/create_brat_lyrics_video_legacy.py`

- default `--max-words 6`

### Sentence / clause, offline

`/resolved/skill/path/scripts/create_brat_lyrics_video_offline.py`

### Legacy, offline

`/resolved/skill/path/scripts/create_brat_lyrics_video_offline_legacy.py`

Offline TTS engines generally do not expose Edge-style WordBoundary events. Offline generators derive deterministic source-token timings from the final synthesized audio and must mark `timing_mode: estimated-from-offline-audio`.

## Preserve the format

- 1:1 canvas, 1080 × 1080, 30 fps.
- Preserve capitalization, punctuation, and every source token.
- Reveal complete words only.
- At every spoken or estimated word boundary, hard-cut to a newly recomputed layout of the active text block.
- Never add fades, tweens, crossfades, motion blur, colored emphasis, black scenes, or character-by-character typing unless requested.
- Fit a narrow sans-serif block inside roughly 74% width and 68% height.
- Center the block, left-align lines, stretch glyphs slightly, then downsample/upscale for the soft low-resolution Brat texture.

## Workflow

1. Resolve this skill directory by matching the `name` frontmatter.
2. Ask/resolve voice, background, and grouping mode.
3. Inspect runtime capabilities: `ffmpeg`, `ffprobe`, Python, Edge dependency/network path, `say`, `espeak-ng`, `espeak`.
4. Try the selected voice through the preferred backend without changing the user's creative choice.
5. Select the generator corresponding to `legacy` vs `sentence/clause`.
6. Render an MP4 and manifest.
7. Inspect manifest:
   - `source_words == displayed_words`;
   - ordered `words[].shown` exactly equals whitespace-tokenized source;
   - grouping boundaries follow the selected mode;
   - offline render records `requested_voice`, `tts_backend`, `actual_voice`, `timing_mode`.
8. Inspect a contact sheet and at least one full-resolution frame.
9. Validate H.264, AAC, 1080 × 1080, 30 fps, audio/video presence, and matching duration.
10. Return the persistent MP4 link and report actual rendering details.

## Example user-choice prompt

When choices are missing, ask approximately:

**Hlas:** Vlasta / Antonín / custom Edge / offline female / offline male / eSpeak. Vlasta a Antonín mají nejlepší kvalitu, ale v Codex Online mohou selhat při blokované síti; eSpeak má nižší kvalitu, ale bývá nejspolehlivější offline Linux fallback.  
**Pozadí:** white / brat-green / vlastní hex.  
**Dělení textu:** legacy *(doporučeno; původní krátké bloky cca 6 slov)* / sentence *(celá věta)* / clause *(kompromis, typicky 10 slov a bezpečná interpunkce)*.

## Quality gate

Reject/regenerate if:

- source tokens are missing, duplicated, or reordered;
- grouping does not follow the user's selected mode;
- `legacy` fails to hard-reset at the configured word limit;
- `sentence` resets before sentence-ending punctuation;
- `clause` resets at an unsafe location rather than permitted punctuation;
- selected background differs;
- an offline fallback is falsely reported as an Edge neural voice;
- actual backend/voice is omitted after fallback;
- text touches the frame edge or is illegible;
- Czech pronunciation/backend is inappropriate;
- output lacks audio or video.

Do not reject a valid offline render solely because estimated offline timing is less acoustically precise than Edge WordBoundary timing. Report the distinction clearly.
