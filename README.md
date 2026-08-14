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

## Requirements

captr's core has **no Python dependencies**. It needs, on the system:

- **ffmpeg / ffprobe** built with libass (the `ass` filter)
- a **whispr** clone, pointed to with `--whispr` or `$WHISPR_DIR`, plus a whispr
  backend (e.g. `pip install faster-whisper`)

## Quick start

With the Makefile (venv + captr + a whisper backend + an ffmpeg/libass check):

```bash
make install                                  # venv + captr + faster-whisper + ffmpeg check
make whispr                                   # clone the sibling whispr if you don't have it
make burn VIDEO=myclip.mp4 STYLE=pop          # animated word-by-word subtitles
make check                                    # sanity-check imports, styles and CLI
```

`make help` lists every target. On Python ≥ 3.13, `make install` also adds
`audioop-lts` (which `pydub` needs there). Manual setup instead:

```bash
# 1. get whispr (captr drives it) and a backend
git clone https://github.com/franckferman/whispr
export WHISPR_DIR=$PWD/whispr

# 2. install captr (exposes the `captr` command) and a whispr backend
cd captr
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install faster-whisper

# 3. run it on any short video
captr myclip.mp4 --style film --lang en -o out.mp4        # clean subtitles
captr myclip.mp4 --style pop  --lang en -o out_pop.mp4    # animated word-by-word
```

No video handy? Make a 3-second test clip with speech:

```bash
espeak-ng -w a.wav "Captr burns styled subtitles onto a video."
ffmpeg -f lavfi -i color=c=0x102030:s=1280x720 -i a.wav -shortest -pix_fmt yuv420p clip.mp4
captr clip.mp4 --style pop --lang en -o out.mp4
```

## Usage

```bash
# Clean cinematic subtitles
captr talk.mp4 --style film --lang en -o subtitled.mp4

# Animated word-by-word captions (TikTok/Reels) -- uses whispr word timings
captr talk.mp4 --style pop --lang en -o captions.mp4
# ...with higher-accuracy word alignment (needs whispr's align extra)
captr talk.mp4 --style pop --lang en --word-provider stable_ts -o captions.mp4

# Translate, then subtitle in the target language
captr talk.mp4 --style translation --lang en --translate-to fr -o sous-titre.mp4

# Soft, toggleable subtitle track instead of burning (Matroska)
captr talk.mp4 --style film --soft -o soft.mkv

# Vertical 9:16 footage (Shorts/Reels safe area)
captr short.mp4 --style pop-vertical --lang en -o short_captions.mp4

# Just emit the .ass to tweak by hand
captr talk.mp4 --style film --ass-only
```

Or as a module: `python -m captr.cli video.mp4 --style film`.

## Styles

| Preset | Look |
|---|---|
| `film` | bottom-centred, clean sans-serif, white + thin outline — cinematic, out of the way |
| `translation` | like `film`, a touch smaller/dimmer — a discreet translated overlay |
| `pop` | big bold centred, **word-by-word animated** (karaoke), active word highlighted |
| `film-vertical` | `film` raised into the 9:16 safe area |
| `pop-vertical` | `pop`, sized and raised for vertical video |

A style is a `StyleSpec` (`captr/ass.py`): font, size, colours, outline,
position, and `word_level`. Adding one is a few lines. Word-animated styles
(`word_level=True`) make captr request per-word timestamps from whispr
automatically.

## How it works

- `captr/transcribe.py` — drives whispr as a subprocess, returns its JSON
  (segments, optional word timings, optional translation).
- `captr/ass.py` — `StyleSpec` + `build_ass()` render segments to an ASS document.
- `captr/styles/` — the presets.
- `captr/burn.py` — ffmpeg/libass burn (`-vf ass=...`), audio stream-copied.
- `captr/cli.py` — orchestrates the three.

## Roadmap

- [x] `film` / `translation` presets (segment-level), end-to-end burn
- [x] `pop` — animated word-by-word captions, consuming whispr's
      `--word-timestamps` (native or stable_ts/whisperx alignment)
- [x] soft-subtitle output (`--soft`, mux `.ass` into Matroska instead of burning)
- [x] vertical (9:16) safe-area presets (`film-vertical`, `pop-vertical`)
- [ ] per-word "one word at a time" pop variant (vs cumulative karaoke)
- [ ] `.srt` soft-sub export for players without ASS

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0).
