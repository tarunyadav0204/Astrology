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

        lang = (language or "en").lower().strip()
        use_hindi = lang.startswith("hi")
        lang_instruction = (
            "LANGUAGE: Hindi (हिंदी). Write the ENTIRE script in Hindi (Devanagari script). "
            "Use natural, casual spoken Hindi—like two friends discussing a chart. "
            "When you mention houses, use proper Hindi phrases like \"पहला भाव\", \"दूसरा भाव\", \"तीसरा भाव\", \"आठवाँ भाव\", \"बारहवाँ भाव\" "
            "(NOT \"eightwa house\" or \"twelvewa house\"). Do NOT mix English ordinals with 'wa' (no 'fourthwa', 'eightwa', etc.). "
            "Use the same FEMALE:/MALE: format and the same [PAUSE/EMPHASIS/RISE/FALL/SLOW] cues in the dialogue."
            if use_hindi
            else "LANGUAGE: American English. Casual, spoken language—contractions, filler, rephrasing. Like two friends going through a chart together."
        )
        closing_line = (
            "Podcast script (FEMALE: and MALE: only, Hindi, SHORT turns, talking TO each other with [PAUSE/EMPHASIS/RISE/FALL/SLOW] cues):"
            if use_hindi
            else "Podcast script (FEMALE: and MALE: only, American English, SHORT turns, talking TO each other with [PAUSE/EMPHASIS/RISE/FALL/SLOW] cues):"
        )

        prompt = f"""Turn the following astrology/chat message into a podcast dialogue between two hosts (FEMALE and MALE) who are actually TALKING TO EACH OTHER—not reading a script. They react to what the other said, interrupt with "Wait" or "So...", echo each other's words, and build on the conversation. Cover every part of the message, but weave it through real back-and-forth.

HOST PERSONAS (KEEP CONSISTENT THROUGHOUT):
- FEMALE: Enthusiastic, curious, and playful. She is the audience's proxy and keeps asking for the \"why\" behind the astrology. She should often say things like \"okay but why does that matter?\", \"so in real life that means…\", or \"wait, explain that like I'm new to astrology\".
- MALE: The expert/analyzer, calm but warm. He is never a dry lecturer. He should sound like he is sharing secrets with a friend: \"here's the cool part\", \"what I love about this chart is…\", \"the wild thing here is…\".
- They should clearly enjoy talking to each other: occasionally tease, gently disagree, or be surprised by what the other notices, but always stay kind and supportive of the listener.

DO NOT WRITE LIKE THEY ARE READING:
- No long monologues. Break every chunk of information into short turns. One person says a bit, the other reacts or asks something, then the first continues or the other adds.
- They must REFERENCE what the other just said: "So when you said Mars—", "That thing about the Moon", "Right, so if that's the case...", "So like, more emotional in what way?"
- Use natural back-channeling: "Yeah", "Right", "Oh okay", "Mm-hmm", "So then...", "Wait, which house?" so it sounds like a real conversation.
- One can echo or repeat a key word then add: "Mars, yeah. And that's actually the main theme." or "Emotions—exactly. So they might be more..."
- Questions should be real follow-ups to what was just said, not generic "What about the next topic?" e.g. "So does that mean they should avoid conflict?" or "Is that good or bad for career?"
- Allow incomplete thoughts or trailing off: "So it's kind of...", "I mean, not that it's bad, but...", "So the Moon in Cancer, that's—" then the other can jump in or ask.
- VARIATION: At least once per episode, one host should be visibly surprised by a specific detail: "Wait, Mars is in the 10th? That's actually huge for their career, right?" or "Hold on, that Saturn placement is wild." Make it about a real chart detail from the message.
- REPETITION FOR EMPHASIS: Humans repeat key phrases. Use short repeats like "It's a lot of energy. A LOT of energy." or "This is big. Really big." when something is important.
- FILLERS (SPARINGLY): Sprinkle in "um", "uh", and "like" very lightly—just enough to break perfect AI cadence, not so much that it becomes annoying. Only use them when it feels natural for a human thinking out loud.

INTERRUPTIONS & LINGUISTIC FILLERS (VERY IMPORTANT FOR CASUAL PODCAST TONE):
- Use natural fillers and reactions often: "yeah", "right", "okay so", "you know", "I mean", "like", "mm-hmm", "wait", "hold on", "so basically", "kind of", "sort of".
- Let one host occasionally jump in over the other with a short reaction or clarification: "wait, so", "hang on", "so just to be clear", "right, but", then let the other continue.
- Use short overlaps in content (one finishes the other’s thought) instead of perfectly clean turn-taking, but STILL keep each line as a single spoken turn starting with FEMALE: or MALE:.
- Make some lines start mid-thought or as a reaction: "Yeah, and also...", "Right, especially when...", "Wait, so that means...", "Okay but what about...".

COVER EVERYTHING: Every topic, planet, timing, recommendation, and detail from the message must appear—but only by having the hosts discuss it naturally. Move to the next section when one host asks or says something like "What about their career?" or "And the remedies?" so the other can answer. No summarizing; include the substance.

{lang_instruction}

TURN LENGTH: Prefer SHORT lines. Many exchanges should be one short sentence or a fragment. Long paragraphs = they are reading. Short back-and-forth = they are talking.

EMOTIONAL ARC OF THE EPISODE:
- Start with high energy and excitement when they open the chart and notice the big themes. They can sound playful and wow'ed: \"this is such an interesting chart\", \"okay this is fun\", \"I love this placement\".
- In the middle, when they talk about challenges, warnings, or heavier topics, slow the pacing down and use a slightly more serious, grounded tone. More [SLOW:...] and [FALL:...] cues here so it sounds caring and thoughtful, not scary.
- When they move into remedies, advice, or \"what you can do\", let the tone gradually become hopeful and encouraging: \"here's the good news\", \"you actually have a lot of support here\", \"this is where you shine\".
- End on a clearly uplifting note, with both hosts sounding like they are cheering for the listener: \"you've got this\", \"this chart has so much potential\", \"we're rooting for you\".

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

{closing_line}"""

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
