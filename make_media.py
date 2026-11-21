"""Makes the page's media from the finished videos in ../ad-video-workflow/ads and ../animation-workflow/build:

  media/<key>.mp4   a web copy (H.264, CRF 24, AAC 128k, fast start)
  media/<key>.jpg   the poster frame
  media/cuts.js     where each cut falls in each script, for the marked scripts on the page

Run it again after a video changes: python make_media.py
"""
import difflib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).parent
ADS = HERE.parent / 'ad-video-workflow' / 'ads'
ANIMATION = HERE.parent / 'animation-workflow'
MEDIA = HERE / 'media'
VIDEOS = {  # key on the page: (folder, poster time in s)
    'giza': ('giza-pyramid-history', 7.0),
    'spf': ('sunscreen-spf-beauty', 3.8),
    'sky': ('blue-sky-explainer', 2.6),
}
ANIMATED = {  # key on the page: (render, poster time in s). Its marks are where sound.py starts each narration line.
    'mactan': (ANIMATION / 'build' / 'mactan_blender_vo.mp4', 3.0),
    'dalton': (ANIMATION / 'build' / 'dalton_blender_vo.mp4', 3.0),
    'bataan': (ANIMATION / 'build' / 'bataan_blender_vo.mp4', 3.0),
    'corregidor': (ANIMATION / 'build' / 'corregidor_unreal_vo.mp4', 3.0),
}
ALSO = {  # other cuts of a video, shown in its notes: key: (file, poster time in s). No marks of their own.
    'giza-remotion': (ADS / 'giza-pyramid-history' / 'giza-pyramid-history-remotion.mp4', 7.0),
    'mactan-portrait': (ANIMATION / 'build' / 'mactan_portrait_blender_vo.mp4', 3.0),
    'mactan-unreal': (ANIMATION / 'build' / 'mactan_unreal_vo.mp4', 3.0),
    'dalton-unreal': (ANIMATION / 'build' / 'dalton_unreal_vo.mp4', 3.0),
}
NUMBERS = {'two': '2', 'five': '5'}  # Whisper spells some numbers out


def tokens(text):
    """Words as bare lowercase tokens: '93%,' gives '93' 'percent', '20-50' gives '20' '50'."""
    text = text.lower().replace('%', ' percent ').replace('-', ' ')
    return [NUMBERS.get(t, t) for t in re.sub(r"[^a-z0-9 ]", '', text).split()]


def heard(words):
    """Whisper's words with split numbers joined again ('3' ',700' is one word), as (token, start) pairs."""
    joined = []
    for w in words:
        if joined and w['w'] and not w['w'][0].isalnum():
            joined[-1]['w'] += w['w']
        else:
            joined.append(dict(w))
    return [(t, w['start']) for w in joined for t in tokens(w['w'])]


def word_starts(script, words):
    """When the narrator starts each word of the script, or None where Whisper heard something else."""
    spoken = heard(words)
    owner = [(i, t) for i, word in enumerate(script.split()) for t in tokens(word)]
    starts = [None] * len(script.split())
    match = difflib.SequenceMatcher(None, [t for _, t in owner], [t for t, _ in spoken], autojunk=False)
    for block in match.get_matching_blocks():
        for k in range(block.size):
            i = owner[block.a + k][0]
            if starts[i] is None:
                starts[i] = spoken[block.b + k][1]
    return starts


def load_timeline(folder):
    spec = importlib.util.spec_from_file_location(f'tl_{folder.name}', folder / 'timeline.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def marks(folder):
    """[(index of the script word the cut lands before, cut time)], plus when the credits start."""
    tl = load_timeline(folder)
    script = json.loads((folder / 'vo' / 'vo.json').read_text(encoding='utf-8'))['text']
    starts = word_starts(script, tl.WORDS)
    cuts = sorted({0.0, *[t for name, t in tl.CUT.items() if name != 'credits']})
    out = []
    for c in cuts:
        i = 0 if c == 0 else next(i for i, s in enumerate(starts) if s is not None and s > c)
        assert starts[i] - c < 0.2, f'{folder.name}: no word starts just after the cut at {c}'
        out.append((i, round(c, 3)))
    return script, out, round(tl.CUT['credits'], 3)


def line_marks(folder):
    """[(index of the script word a narration line opens with, when it starts)] from an animation's sound.py."""
    spec = importlib.util.spec_from_file_location(f'sound_{folder.name}', folder / 'sound.py')
    sound = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sound)
    script, out = [], []
    for start, _, text in sound.LINES:
        out.append((len(script), round(start, 3)))
        script += text.split()
    return ' '.join(script), out, sound.SECONDS


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', *map(str, args)], check=True)


def web(src, poster, key):
    """The web copy and the poster frame of one video."""
    ffmpeg('-i', src, '-c:v', 'libx264', '-crf', 24, '-preset', 'slow', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', MEDIA / f'{key}.mp4')
    ffmpeg('-ss', poster, '-i', src, '-frames:v', 1, '-vf', "scale='min(1280,iw)':-2", '-q:v', 4, MEDIA / f'{key}.jpg')


def main():
    MEDIA.mkdir(exist_ok=True)
    data = {}
    for key, (name, poster) in VIDEOS.items():
        folder = ADS / name
        src = folder / f'{name}-v1.mp4'
        if 'data' not in sys.argv[1:]:
            web(src, poster, key)
        script, cut_marks, credits = marks(folder)
        data[key] = {'marks': cut_marks, 'credits': credits}
        print(key, len(cut_marks), 'cuts:', ' | '.join(' '.join(script.split()[i:i + 3]) for i, _ in cut_marks))
    for key, (src, poster) in ANIMATED.items():
        if 'data' not in sys.argv[1:]:
            web(src, poster, key)
        script, cut_marks, end = line_marks(ANIMATION / key)
        data[key] = {'marks': cut_marks, 'credits': end}
        print(key, len(cut_marks), 'lines:', ' | '.join(' '.join(script.split()[i:i + 3]) for i, _ in cut_marks))
    for key, (src, poster) in ALSO.items():
        if 'data' not in sys.argv[1:]:
            web(src, poster, key)
    (MEDIA / 'cuts.js').write_text('// Written by make_media.py: [index of the script word a cut lands before, cut time in s]\n'
                                   f'window.CUTS = {json.dumps(data)};\n', encoding='utf-8')


if __name__ == '__main__':
    main()
