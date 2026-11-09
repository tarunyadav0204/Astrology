"""The optional presenter package is deliberately fixed at two five-second takes."""
import hashlib
import json
import random
from pathlib import Path

from db import execute, get_conn

MODEL = "gemini-omni-1.1-flash"
RESOLUTION = "360p"
SECONDS = 5

IDENTITY = (
    "The adult Indian woman in the supplied reference is the AstroRoshni presenter, not the chart native. "
    "Preserve her facial identity: face shape, eyes, eyebrows, nose, lips, skin tone, apparent age, "
    "small bindi and shoulder-length side-parted wavy dark hair. Do not recast or beautify her into "
    "a different person. Warm, composed, approachable, with realistic skin texture."
)

OUTFITS = (
    'a rich plum silk saree with a fine antique-gold woven border and a matching tailored blouse',
    'a midnight-blue silk saree with restrained silver zari detailing and a matching blouse',
    'a muted rose silk saree with delicate champagne-gold embroidery and a matching blouse',
    'an ivory silk saree with a refined copper-gold border and a warm copper blouse',
    'a deep teal silk saree with a narrow gold border and a matching blouse',
    'a warm terracotta silk saree with subtle bronze motifs and a matching blouse',
)
SETS = (
    'an elegant walnut astrology library with softly lit book niches, an understated brass celestial sculpture and cream walls',
    'a refined sandstone consultation studio with a curved niche, a small brass armillary sphere and soft amber wall lighting',
    'a contemporary midnight-blue astrology studio with fine brass celestial linework, a warm desk lamp and subtle depth of field',
    'an airy ivory-and-oak study beside a softly curtained window, with a tasteful bronze sundial and one indoor plant',
    'a sophisticated muted-plum studio with warm wood paneling, a discreet celestial wall artwork and soft practical lighting',
    'a calm sage-and-cream consultation room with a fluted oak wall, a small brass astronomical ornament and warm indirect lighting',
)


def reference_image() -> bytes:
    path = Path(__file__).with_name('assets') / 'presenter-reference.png'
    if not path.is_file() or not path.stat().st_size:
        raise RuntimeError('The approved presenter reference image is missing.')
    return path.read_bytes()


def choose_look(previous: dict | None = None, *, rng=None) -> dict:
    """Change both outfit and set; retain the selected look for retries."""
    rng = rng or random.SystemRandom()
    previous = previous or {}
    return {'outfit': rng.choice([v for v in OUTFITS if v != previous.get('outfit')]),
            'background': rng.choice([v for v in SETS if v != previous.get('background')])}


def prepare_presenter(user_id: int, job_id: str, plan: dict) -> tuple[bytes, dict]:
    reference = reference_image()  # Fail before any paid asset calls if missing.
    digest = hashlib.sha256(reference).hexdigest()
    look = plan.get('presenter_look')
    if look:
        if look.get('reference_sha256') != digest:
            raise RuntimeError('The approved presenter reference changed during this generation.')
        if not look.get('outfit') or not look.get('background'):
            raise RuntimeError('The saved presenter look is incomplete.')
        return reference, look
    with get_conn() as conn:
        rows = execute(conn, '''SELECT plan_json FROM reel_render_jobs
            WHERE user_id=%s AND id<>%s ORDER BY created_at DESC LIMIT 50''', (user_id, job_id)).fetchall()
        previous = next((p['presenter_look'] for row in rows
                         if (p := json.loads(row[0])).get('presenter_look')), None)
        look = {**choose_look(previous), 'reference_sha256': digest, 'identity': 'approved-presenter-v1'}
        plan['presenter_look'] = look
        execute(conn, 'UPDATE reel_render_jobs SET plan_json=%s WHERE id=%s', (json.dumps(plan), job_id))
        conn.commit()
    return reference, look


def portrait_prompt(look: dict) -> str:
    return (
        f'Create a photorealistic vertical 9:16 presenter portrait by editing the supplied identity photograph. {IDENTITY} '
        'Use that photograph for identity and hairstyle only; replace its emerald saree and its original room. '
        f'NEW WARDROBE: {look["outfit"]}. Small elegant gold earrings, natural professional makeup. '
        f'NEW BACKGROUND: {look["background"]}. '
        'Show her seated at a tasteful desk, eye-level straight-on medium portrait, face and hands fully inside '
        'the vertical safe area. Face unobstructed, lips relaxed, looking into the camera. '
        'Soft flattering cinematic light, natural proportions, polished premium Indian editorial photography. '
        'This single portrait is the visual reference for both opening and closing of the same reel. '
        'No additional people, text, captions, charts, watermarks or invented logos.'
    )


def validate_presenter_beats(beats: list[dict]) -> None:
    if len(beats) < 2 or beats[0].get('type') != 'opening' or beats[-1].get('type') != 'closing':
        raise ValueError('Presenter reels require opening first and closing last.')
    errors = []
    for role, beat in (('opening', beats[0]), ('closing', beats[-1])):
        line = str(beat.get('narration') or '').strip()
        words = len(line.split())
        if not line or words > 10:
            errors.append(f'Presenter {role} has {words} words; rewrite only this line as one complete sentence of 5–10 words for five seconds.')
    if errors:
        raise ValueError('\n'.join(errors))


def video_prompt(line: str, language: str, role: str) -> str:
    spoken_language = 'natural Hindi, entirely in Hindi' if language == 'hi' else 'English with a natural Indian accent'
    date_direction = ('Pronounce any dates, months, years and times entirely in Hindi, never in English. '
                      if language == 'hi' else '')
    return (
        f'Create exactly {SECONDS} seconds of portrait 9:16 presenter video with audible synchronized speech. '
        f'{IDENTITY} Match the supplied reference woman exactly: same face, hair, attire, lighting and set. '
        f'This is the {role} of a personal astrology explanation. She looks at the camera and speaks '
        f'in {spoken_language}, in a warm clear adult female voice, calm conversational delivery. '
        'Use the same vocal character for both takes. No music, no voice-over, no other speaker, '
        'no captions, no chart, no invented logo or additional words. A steady locked camera, subtle natural gestures. '
        'Begin speaking within 0.2 seconds, finish the complete sentence by 4.5 seconds, then hold a warm expression. '
        f'{date_direction}Say ONLY this exact approved line, once: {line}'
    )
