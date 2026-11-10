"""Gemini story direction, with the same JSON contract and per-call cost ledger."""
import os
from types import SimpleNamespace

import httpx
from . import costs

MODEL = 'gemini-3-flash-preview'


def create(stage, *, input, text, max_output_tokens, store=False):
    key = os.environ['GEMINI_API_KEY']
    schema = text['format']['schema']
    with costs.attempt(stage, MODEL) as event:
        response = httpx.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent',
            headers={'x-goog-api-key': key}, timeout=180,
            json={'contents': [{'role': 'user', 'parts': [{'text': input}]}],
                  'generationConfig': {'responseMimeType': 'application/json',
                                       'responseJsonSchema': schema,
                                       'maxOutputTokens': max_output_tokens,
                                       'thinkingConfig': {'thinkingLevel': 'low'}}})
        response.raise_for_status()
        data = response.json()
        usage = data.get('usageMetadata') or {}
        output = usage.get('candidatesTokenCount')
        metered = {'input_tokens': usage.get('promptTokenCount'),
                   'input_tokens_details': {'cached_tokens': usage.get('cachedContentTokenCount', 0)},
                   'output_tokens': None if output is None else output + usage.get('thoughtsTokenCount', 0),
                   'thinking_tokens': usage.get('thoughtsTokenCount', 0)}
        event.finish(metered, data.get('responseId'))
        candidates = data.get('candidates') or []
        if not candidates or candidates[0].get('finishReason') != 'STOP':
            raise RuntimeError('Gemini story generation did not complete')
        output_text = ''.join(part.get('text', '') for part in candidates[0].get('content', {}).get('parts', []) if not part.get('thought'))
        if not output_text.strip():
            raise RuntimeError('Gemini returned an empty story')
        return SimpleNamespace(output_text=output_text, usage=metered, id=data.get('responseId'))
