<div align="center">

# captr

**Burn styled subtitles onto a video — powered by [whispr](https://github.com/franckferman/whispr) + libass.**

</div>

---

## What it is

Give captr a video; it transcribes it with whispr, renders the transcript to an
ASS subtitle file with a chosen **style preset**, and burns it onto the video
with ffmpeg/libass.

```
video ──▶ whispr (ASR + optional translation, word timings) ──▶ captr (ASS style) ──▶ ffmpeg/libass ──▶ subtitled video
```

captr does **not** re-implement speech recognition — that is whispr's job. captr
owns what whispr doesn't: **the look**.

## Install

captr's core has no Python dependencies. It needs, on the system:

- **ffmpeg / ffprobe** built with libass (the `ass` filter)
- a **whispr** clone, pointed to with `--whispr` or `$WHISPR_DIR`, plus a whispr
  backend (e.g. `pip install faster-whisper`)

```bash
git clone https://github.com/franckferman/whispr   # captr drives this
export WHISPR_DIR=$PWD/whispr
```

## Usage

```bash
# Clean cinematic subtitles
captr talk.mp4 --style film --lang en -o subtitled.mp4

# Translate, then subtitle in the target language
captr talk.mp4 --style translation --lang en --translate-to fr -o sous-titre.mp4

# Just emit the .ass (no burn) to tweak by hand
captr talk.mp4 --style film --ass-only
```

Or as a module: `python -m captr.cli video.mp4 --style film`.

## Styles

| Preset | Look |
|---|---|
| `film` | bottom-centred, clean sans-serif, white + thin outline — cinematic, out of the way |
| `translation` | like `film`, a touch smaller/dimmer — reads as a discreet translated overlay |
| `pop` *(planned)* | word-by-word animated captions (TikTok/Reels), active word highlighted |

A style is a `StyleSpec` (`captr/ass.py`): font, size, colours, outline,
position. Adding one is a few lines.

## How it works

- `captr/transcribe.py` — drives whispr as a subprocess, returns its JSON
  (segments, optional word timings, optional translation).
- `captr/ass.py` — `StyleSpec` + `build_ass()` render segments to an ASS document.
- `captr/styles/` — the presets.
- `captr/burn.py` — ffmpeg/libass burn (`-vf ass=...`), audio stream-copied.
- `captr/cli.py` — orchestrates the three.

## Roadmap

- [x] `film` / `translation` presets (segment-level), end-to-end burn
- [ ] `pop` — animated word-by-word captions, consuming whispr's
      `--word-timestamps` (native or stable_ts/whisperx alignment)
- [ ] soft-subtitle output (mux `.ass`/`.srt` instead of burning)
- [ ] vertical (9:16) safe-area presets

## License

TBD.
