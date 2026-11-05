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
