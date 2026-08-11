PYTHON   := python3
VENV     := .venv
PIP      := $(VENV)/bin/pip
PY       := $(VENV)/bin/python

# ── Config (override with make VAR=value) ─────────────────────────────────────
VIDEO      ?=
STYLE      ?= film
LANGUAGE   ?=
BACKEND    ?= faster_whisper
OUTPUT     ?=
WHISPR_DIR ?= ../whispr

.DEFAULT_GOAL := help

# ── Setup ─────────────────────────────────────────────────────────────────────

.PHONY: venv
venv: ## Create the virtualenv
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip --quiet

.PHONY: deps
deps: venv ## Install captr (core has no runtime pip deps; needs ffmpeg+libass)
	$(PIP) install --quiet -e .

.PHONY: deps-backend
deps-backend: deps ## Install a whisper backend so captr can transcribe (faster-whisper + whispr runtime deps)
	$(PIP) install --quiet faster-whisper ffmpeg-python tqdm requests pydub
	@$(PY) -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,13) else 1)' \
	  && { echo "[+] Python >= 3.13: installing audioop-lts (pydub needs it)"; $(PIP) install --quiet audioop-lts; } \
	  || true

.PHONY: install
install: deps-backend check-ffmpeg ## Full install (venv + captr + backend + ffmpeg check)
	@echo "[+] captr ready. Point --whispr at a whispr clone (or set \$$WHISPR_DIR)."

.PHONY: whispr
whispr: ## Clone the sibling whispr project if missing (WHISPR_DIR=../whispr)
	@test -d $(WHISPR_DIR) || git clone --depth=1 https://github.com/franckferman/whispr $(WHISPR_DIR)
	@echo "[+] whispr at $(WHISPR_DIR) (install its backend: make -C $(WHISPR_DIR) deps-faster-whisper)"

# ── Checks ────────────────────────────────────────────────────────────────────

.PHONY: check-ffmpeg
check-ffmpeg: ## Verify ffmpeg has the libass 'ass' filter (needed to burn subtitles)
	@ffmpeg -hide_banner -filters 2>/dev/null | grep -qw ass \
	  && echo "[+] ffmpeg libass ('ass' filter) present" \
	  || { echo "[x] ffmpeg lacks the 'ass' filter (libass). Install an ffmpeg built with libass."; exit 1; }

.PHONY: check
check: ## Validate imports, styles and CLI
	$(PY) -c "import captr, captr.ass, captr.burn; print('modules   OK')"
	$(PY) -c "from captr.styles import STYLES; print('styles    OK ->', ', '.join(STYLES))"
	$(PY) -m captr.cli --help >/dev/null && echo "CLI       OK"

# ── Run ───────────────────────────────────────────────────────────────────────

.PHONY: burn
burn: ## Burn subtitles onto VIDEO= (STYLE=film|translation|pop|film-vertical|pop-vertical)
ifndef VIDEO
	$(error Specify VIDEO=path/to/video.mp4)
endif
	$(PY) -m captr.cli "$(VIDEO)" --style $(STYLE) --backend $(BACKEND) \
	  $(if $(LANGUAGE),--lang $(LANGUAGE),) $(if $(OUTPUT),--output "$(OUTPUT)",) \
	  --whispr $(WHISPR_DIR)

.PHONY: soft
soft: ## Soft-mux a toggleable subtitle track instead of burning
ifndef VIDEO
	$(error Specify VIDEO=path/to/video.mp4)
endif
	$(PY) -m captr.cli "$(VIDEO)" --style $(STYLE) --backend $(BACKEND) --soft \
	  $(if $(LANGUAGE),--lang $(LANGUAGE),) $(if $(OUTPUT),--output "$(OUTPUT)",) \
	  --whispr $(WHISPR_DIR)

.PHONY: translate
translate: ## Burn TRANSLATED subtitles (TO= ISO 639-1, e.g. make translate VIDEO=talk.mp4 TO=en)
ifndef VIDEO
	$(error Specify VIDEO=path/to/video.mp4)
endif
ifndef TO
	$(error Specify TO=<target ISO 639-1 code>, e.g. TO=en)
endif
	$(PY) -m captr.cli "$(VIDEO)" --style translation --backend $(BACKEND) \
	  --translate-to $(TO) $(if $(LANGUAGE),--lang $(LANGUAGE),) --whispr $(WHISPR_DIR)

.PHONY: ass-only
ass-only: ## Emit the .ass subtitle file only (no video render)
ifndef VIDEO
	$(error Specify VIDEO=path/to/video.mp4)
endif
	$(PY) -m captr.cli "$(VIDEO)" --style $(STYLE) --backend $(BACKEND) --ass-only \
	  $(if $(LANGUAGE),--lang $(LANGUAGE),) --whispr $(WHISPR_DIR)

# ── Clean ─────────────────────────────────────────────────────────────────────

.PHONY: clean
clean: ## Remove Python caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete

.PHONY: clean-all
clean-all: clean ## Remove the virtualenv too
	rm -rf $(VENV)

# ── Help ──────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help
	@echo ""
	@echo "  captr — burn styled subtitles onto a video (whispr + libass)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	    | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Variables (override with make VAR=value):"
	@echo "    VIDEO       input video"
	@echo "    STYLE       $(STYLE)  (film|translation|pop|film-vertical|pop-vertical)"
	@echo "    BACKEND     $(BACKEND)   LANGUAGE  ISO 639-1 (auto if empty)"
	@echo "    WHISPR_DIR  $(WHISPR_DIR)   TO  translation target (translate)"
	@echo ""
	@echo "  Examples:"
	@echo "    make install"
	@echo "    make burn VIDEO=talk.mp4 STYLE=pop"
	@echo "    make soft VIDEO=talk.mp4 STYLE=film"
	@echo "    make translate VIDEO=talk.mp4 LANGUAGE=fr TO=en"
	@echo "    make check"
	@echo ""
