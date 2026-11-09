"""Use podcast synthesis unchanged, with reel quota and cost accounting per RPC."""
import contextvars
import logging

from google.api_core.exceptions import ResourceExhausted

from reel_studio import costs
from reel_studio.tts_quota import wait_for_tts_slot, cool_down_tts

logger = logging.getLogger(__name__)


class MeteredSpeechClient:
    """The podcast helper runs RPCs in an executor; preserve the reel ledger context.

    Wrap the RPC rather than the whole segment so SSML compatibility attempts,
    chunking and quota retries are all paced and recorded individually.
    """
    def __init__(self, client):
        self.client = client
        self.context = contextvars.copy_context()

    def synthesize_speech(self, **kwargs):
        return self.context.copy().run(self._synthesize, kwargs)

    def _synthesize(self, kwargs):
        voice_name = kwargs['voice'].name
        speech_input = kwargs['input']
        content = speech_input.ssml or speech_input.text
        for attempt in range(4):
            wait_for_tts_slot()
            try:
                with costs.attempt('tts', voice_name, input_format='ssml' if speech_input.ssml else 'text') as event:
                    response = self.client.synthesize_speech(**{**kwargs, 'retry': None, 'timeout': 120})
                    event.finish({'characters': len(content)})
                return response
            except ResourceExhausted:
                cooldown = min(60, 15 * (2 ** attempt))
                cool_down_tts(cooldown)
                logger.warning('REEL_TTS_QUOTA voice=%s attempt=%s cooldown_seconds=%s',
                               voice_name, attempt + 1, cooldown)
                if attempt == 3:
                    raise RuntimeError('Speech generation is temporarily unavailable because the speech provider quota is exhausted. Please try again later.')
