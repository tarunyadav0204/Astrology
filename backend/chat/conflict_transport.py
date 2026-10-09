"""One server-owned Responses WebSocket, with reconnectable transcript state."""
import asyncio
import json
import os
import websockets
from chat.conflict_contract import strict_schema

class ConflictModelConnection:
    def __init__(self, model):
        self.model = model
        self.socket = None
        self.previous_id = None

    async def __aenter__(self):
        key = os.getenv('OPENAI_API_KEY')
        if not key:
            raise RuntimeError('Conflict resolution is temporarily unavailable')
        self.socket = await websockets.connect('wss://api.openai.com/v1/responses',
            extra_headers={'Authorization': f'Bearer {key}'}, open_timeout=20,
            close_timeout=5, max_size=8 * 1024 * 1024, ping_interval=20)
        return self

    async def __aexit__(self, *args):
        if self.socket:
            await self.socket.close()

    async def turn(self, instructions, transcript):
        from ai.gemini_chat_analyzer import resolve_openai_reasoning_effort
        request = dict(type='response.create', model=self.model, instructions=instructions,
            input=transcript if self.previous_id is None else [transcript[-1]], store=False,
            max_output_tokens=5000, text={'format': {'type': 'json_schema', 'name': 'conflict_resolution', 'strict': True, 'schema': strict_schema()}})
        if self.previous_id:
            request['previous_response_id'] = self.previous_id
        effort = resolve_openai_reasoning_effort(self.model, 'low')
        if effort:
            request['reasoning'] = {'effort': effort}
        await self.socket.send(json.dumps(request))
        async def receive():
            while True:
                event = json.loads(await self.socket.recv())
                kind = event.get('type')
                if kind in {'error', 'response.failed', 'response.incomplete'}:
                    raise RuntimeError('The model could not complete this comparison')
                if kind == 'response.completed':
                    response = event['response']
                    if response.get('status') != 'completed':
                        raise RuntimeError('Incomplete conflict resolution')
                    text = ''.join(part.get('text', '') for item in response.get('output', [])
                        if item.get('type') == 'message' for part in item.get('content', []) if part.get('type') == 'output_text')
                    if not text:
                        raise RuntimeError('Empty conflict resolution')
                    self.previous_id = response['id']
                    return json.loads(text), response
        return await asyncio.wait_for(receive(), timeout=180)
