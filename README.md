# Programmatic Video Editing

A one-page portfolio of three narrated explainers made without AI video: the Great Pyramid (history), what the SPF number means (beauty) and why the sky is blue (science explainer). Each video sits beside its script, marked with a numbered blue-pencil box at every cut. Picking a mark plays the video from that cut, and the phrase being spoken is highlighted as it plays.

Live at https://derpynewb.github.io/programmatic-video-editing/

The footage, photos, music and sound effects are openly licensed and listed in [CREDITS.md](CREDITS.md). The narration is Gemini text-to-speech, and every graphic is drawn in code with Manim and timed to the narrator's words.

## Files

- `index.html` is the whole page. It needs no build step: open it in a browser.
- `media/` holds the web copies of the videos (H.264, CRF 24), their poster frames and `cuts.js`, which lists where each cut falls in each script.
- `make_media.py` makes everything in `media/` from the finished videos, which are built in a separate local project that isn't in this repo. Run `python make_media.py` after a video changes, or `python make_media.py data` to rewrite only `cuts.js`.

## How the cut marks are placed

`make_media.py` loads each video's timeline, takes every cut time, and finds the first script word the narrator starts after it, from the Whisper word times aligned to the script. It stops if that word starts more than 0.2 s after the cut, so a mark can never land on the wrong phrase. The page splits each script at those words.

## Viewing it locally

Opening `index.html` from disk works, and so does any server that supports byte ranges, GitHub Pages included. Python's `http.server` doesn't support ranges, so behind it the browser can't seek, and every mark plays from the start.
