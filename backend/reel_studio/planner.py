"""Gemini story direction, with the same JSON contract and per-call cost ledger."""
import os
from types import SimpleNamespace

import httpx
from . import costs

import logging

logger = logging.getLogger(__name__)

MODEL = 'gemini-3-flash-preview'


def provider_schema(schema):
    """Keep structure/IDs, but validate array lengths after generation.

    Gemini rejects the planner's nested bounded arrays with INVALID_ARGUMENT.
    Scene and presenter length limits remain in the prompt and local validators.
    """
    if isinstance(schema, list):
        return [provider_schema(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    result = {}
    for key, value in schema.items():
        if key in {'minItems', 'maxItems'}:
            continue
        # Property names are data, not JSON Schema keywords.
        if key in {'properties', '$defs'}:
            result[key] = {name: provider_schema(child) for name, child in value.items()}
        else:
            result[key] = provider_schema(value)
    return result


def create(stage, *, input, text, max_output_tokens, store=False):
    key = os.environ['GEMINI_API_KEY']
    schema = provider_schema(text['format']['schema'])
    with costs.attempt(stage, MODEL) as event:
        response = httpx.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent',
            headers={'x-goog-api-key': key}, timeout=180,
            json={'contents': [{'role': 'user', 'parts': [{'text': input}]}],
                  'generationConfig': {'responseMimeType': 'application/json',
                                       'responseJsonSchema': schema,
                                       'maxOutputTokens': max_output_tokens,
                                       'thinkingConfig': {'thinkingLevel': 'low'}}})
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            try:
                provider_error = response.json().get('error', {})
            except (ValueError, AttributeError):
                provider_error = {}
            detail = str(provider_error.get('message', 'Request rejected')).replace(key, '[redacted]')[:1200]
            event.metadata.update(http_status=response.status_code,
                                  provider_status=provider_error.get('status'), provider_message=detail)
            logger.error('REEL_PLANNER_REJECTED stage=%s model=%s status=%s detail=%s', stage, MODEL, response.status_code, detail)
            raise
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
