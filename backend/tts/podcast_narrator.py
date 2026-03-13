"""
Podcast narrator: convert chat message content into a TTS-friendly podcast script using Gemini.
Script is generated only when the user requests podcast (on button click).
"""

import os
import re
from dotenv import load_dotenv

env_paths = [
    ".env",
    os.path.join(os.path.dirname(__file__), "..", ".env"),
]
for p in env_paths:
    if os.path.exists(p):
        load_dotenv(p)
        break


def generate_podcast_script(message_content: str, language: str = "en") -> str:
    """
    Turn chat message content into a single, conversational podcast script suitable for TTS.
    - No markdown, bullets, or headers in output.
    - Flowing prose; optional short intro/outro.
    - language: "en" or "hi" (script language).
    """
    if not message_content or not message_content.strip():
        return ""

    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return _fallback_script(message_content)

        genai.configure(api_key=api_key)
        # Use same analysis model as rest of app (models/ prefix required by API)
        from utils.admin_settings import get_gemini_analysis_model
        model_name = os.getenv("GEMINI_PODCAST_MODEL") or get_gemini_analysis_model()
        model = genai.GenerativeModel(model_name)

        prompt = f"""Turn the following astrology/chat message into a podcast dialogue between two hosts (FEMALE and MALE) who are actually TALKING TO EACH OTHER—not reading a script. They react to what the other said, interrupt with "Wait" or "So...", echo each other's words, and build on the conversation. Cover every part of the message, but weave it through real back-and-forth.

DO NOT WRITE LIKE THEY ARE READING:
- No long monologues. Break every chunk of information into short turns. One person says a bit, the other reacts or asks something, then the first continues or the other adds.
- They must REFERENCE what the other just said: "So when you said Mars—", "That thing about the Moon", "Right, so if that's the case...", "So like, more emotional in what way?"
- Use natural back-channeling: "Yeah", "Right", "Oh okay", "Mm-hmm", "So then...", "Wait, which house?" so it sounds like a real conversation.
- One can echo or repeat a key word then add: "Mars, yeah. And that's actually the main theme." or "Emotions—exactly. So they might be more..."
- Questions should be real follow-ups to what was just said, not generic "What about the next topic?" e.g. "So does that mean they should avoid conflict?" or "Is that good or bad for career?"
- Allow incomplete thoughts or trailing off: "So it's kind of...", "I mean, not that it's bad, but...", "So the Moon in Cancer, that's—" then the other can jump in or ask.

COVER EVERYTHING: Every topic, planet, timing, recommendation, and detail from the message must appear—but only by having the hosts discuss it naturally. Move to the next section when one host asks or says something like "What about their career?" or "And the remedies?" so the other can answer. No summarizing; include the substance.

LANGUAGE: American English. Casual, spoken language—contractions, filler, rephrasing. Like two friends going through a chart together.

TURN LENGTH: Prefer SHORT lines. Many exchanges should be one short sentence or a fragment. Long paragraphs = they are reading. Short back-and-forth = they are talking.

STRICT FORMAT — EXACTLY TWO SPEAKERS:
- You have ONLY two speakers: FEMALE and MALE. Do not use any other labels (no HOST, NARRATOR, GUEST, SPEAKER 1/2, etc.).
- Every line MUST start with exactly "FEMALE:" or "MALE:" then a space, then the spoken line. No other prefixes or markdown.

CRITICAL — AVOID FLAT "ANNOUNCEMENT" SOUND: Do NOT sound like a railway or airport announcement where every sentence has the same tone. The listener must hear clear variation in pace, pitch, and pauses.
- EVERY line MUST contain at least one cue: [PAUSE:short], [PAUSE:medium], [RISE:...], [FALL:...], [SLOW:...], or [EMPHASIS:...]. Never write two or three sentences in a row with no cue.
- Use [PAUSE:short] or [PAUSE:medium] between thoughts so there are real breaths, not one continuous stream.
- Use [RISE:...] on every question or reaction (e.g. [RISE:Really?] [RISE:So what does that mean?]) so questions sound like questions.
- Use [FALL:...] or [SLOW:...] on conclusions, takeaways, or serious points so they sound weighty, not flat.
- Use [EMPHASIS:word or phrase] on the key word in a sentence so it pops. Vary which word you emphasize.

PROSODY CUES (use liberally; they become breaks, pitch, and speed in speech):
- [PAUSE:short] [PAUSE:medium] [PAUSE:long] — real pauses (short between clauses, medium between thoughts, long before sign-off).
- [EMPHASIS:phrase] [RISE:phrase] [FALL:phrase] [SLOW:phrase] — do not put ] inside the phrase.

Example (every line has at least one cue — never flat):
FEMALE: Okay so we've got their chart. [PAUSE:short] [RISE:Where do we start?]
MALE: [FALL:Moon in Cancer.] [PAUSE:medium] That's the big one.
FEMALE: [RISE:Oh yeah?] [PAUSE:short] What does that mean for them?
MALE: So [PAUSE:short] more in tune with feelings right now. [PAUSE:medium] [SLOW:Like, things might hit different.]
FEMALE: So like [RISE:more sensitive?]
MALE: Yeah. [PAUSE:short] Not in a bad way—just [EMPHASIS:aware]. [FALL:So maybe don't make huge decisions when you're super emotional.]
FEMALE: Got it. [PAUSE:short] [RISE:What about Mars?]
MALE: [EMPHASIS:Mars] is strong. [PAUSE:medium] So energy, drive—that's there. [FALL:Good for taking action.]

Example of the WRONG kind (reading):
MALE: The Moon in Cancer suggests the native is more emotionally aware. Mars in the chart indicates strong energy. (Too long, no reaction from the other person.)

Message to convert (cover every part, but as a real conversation):

{message_content}

Podcast script (FEMALE: and MALE: only, American English, SHORT turns, talking TO each other with [PAUSE/EMPHASIS/RISE/FALL/SLOW] cues):"""

        response = model.generate_content(prompt)
        if not response or not response.text:
            return _fallback_script(message_content)

        script = response.text.strip()
        # Strip any remaining markdown/artifacts
        script = re.sub(r"\s*[\*#]+\s*", " ", script)
        script = re.sub(r"\n{3,}", "\n\n", script)
        return script
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Podcast script generation failed: %s", e)
        return _fallback_script(message_content)


def _fallback_script(message_content: str) -> str:
    """Strip markdown and return a single-speaker script (FEMALE:) when Gemini is unavailable."""
    text = message_content
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    plain = text.strip() or message_content.strip()
    return f"FEMALE: {plain}" if plain else ""
