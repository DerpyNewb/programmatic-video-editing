# Programmatic Video Editing

A one-page portfolio of nine narrated explainers made without AI video: the Great Pyramid (history), what the SPF number means (beauty), why the sky is blue (science explainer), and the Battles of Mactan, Balete Pass, Bataan, Corregidor, Irisan and Leyte (history, animated in Blender and Unreal Engine instead of cut from footage; all but Mactan are vertical, Bataan and Leyte are 3D over real terrain, and Corregidor and Irisan are flat layers at different depths). Each video sits beside its script, marked with a numbered blue-pencil box at every cut. Picking a mark plays the video from that cut, and the phrase being spoken is highlighted as it plays.

Live at https://derpynewb.github.io/programmatic-video-editing/

The footage, photos, music and sound effects are openly licensed and listed in [CREDITS.md](CREDITS.md). The narration is Gemini text-to-speech, and every graphic is drawn in code with Manim and timed to the narrator's words. The Great Pyramid video also has a second cut built in Remotion, from the same voiceover, footage and word timings; its source is in [remotion-giza-explainer](https://github.com/DerpyNewb/remotion-giza-explainer).

## Files

- `index.html` is the whole page. It needs no build step: open it in a browser.
- `media/` holds the web copies of the videos (H.264, CRF 24), their poster frames and `cuts.js`, which lists where each cut falls in each script.
- `make_media.py` makes everything in `media/` from the finished videos, which are built in a separate local project that isn't in this repo. Run `python make_media.py` after a video changes, or `python make_media.py data` to rewrite only `cuts.js`. Its `ANIMATED` list takes the animated videos (the six battles, from `animation-workflow/build`) and marks each where its `sound.py` starts each narration line. Its `ALSO` list adds other cuts of a video (the Remotion cut of the Great Pyramid, Mactan's 9:16 and Unreal renders, and Balete Pass's Unreal render) without marks of their own.

## How the cut marks are placed

`make_media.py` loads each video's timeline, takes every cut time, and finds the first script word the narrator starts after it, from the Whisper word times aligned to the script. It stops if that word starts more than 0.2 s after the cut, so a mark can never land on the wrong phrase. The page splits each script at those words.

## Viewing it locally

Opening `index.html` from disk works, and so does any server that supports byte ranges, GitHub Pages included. Python's `http.server` doesn't support ranges, so behind it the browser can't seek, and every mark plays from the start.
