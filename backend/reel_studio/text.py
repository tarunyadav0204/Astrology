"""Plain copy for speech, storyboard cards, and text rendered inside images."""
import html
import re


def plain_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"```(?:[a-zA-Z]+)?", " ", text)
    # Cover both normal headings and malformed/flattened '###key insights'.
    text = re.sub(r"(?<!\w)#{1,6}[ \t]*(?=\S)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?m)^\s*(?:[-*_]\s*){3,}$", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def speech_punctuation(value: str, language: str) -> str:
    """Remove only a comma incorrectly inserted inside a Hindi compound verb.

    Do not insert timed breaks or split audio requests. Clause-ending commas
    ("सकते हैं, लेकिन") and sentence endings remain untouched.
    """
    if not str(language).lower().startswith('hi'):
        return value
    return re.sub(
        r"(?<![\w\u0900-\u097f])(सकता|सकती|सकते|रहा|रही|रहे|चाहता|चाहती|चाहते|चाहिए)"
        r"\s*[,،]\s*(?=(?:हैं|है|हूँ|हूं|हो|था|थी|थे)(?![\w\u0900-\u097f]))",
        r"\1 ", value,
    )
