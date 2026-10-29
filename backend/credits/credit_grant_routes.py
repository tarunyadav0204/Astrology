"""Admin HTTP API for permanent balance grants and their WhatsApp notice."""
from __future__ import annotations

import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user
from credits.credit_grant_campaigns import (create_credit_grant_campaign, get_credit_grant_recipients_for_whatsapp,
    list_credit_grant_campaigns, mark_credit_grant_whatsapp_queued)
from nudge_engine.task_queue import enqueue_nudge_task
from whatsapp.admin_routes import _find_template, _template_variables
from db import execute, get_conn

router = APIRouter()

class GrantCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    credits: int = Field(..., ge=1, le=10000)
    recipient_ids: List[int] = Field(..., min_length=1, max_length=1000)

def _admin(user: User) -> None:
    if getattr(user, 'role', None) != 'admin':
        raise HTTPException(status_code=403, detail='Admin access required')

def _template_configured() -> bool:
    return bool((os.getenv('CREDIT_GRANT_WHATSAPP_TEMPLATE_NAME') or '').strip())

def _grant_chat_url() -> str:
    """Static URL required by Meta template; may be an AppsFlyer OneLink."""
    return (os.getenv('CREDIT_GRANT_WHATSAPP_CHAT_URL') or 'https://astroroshni.com/chat?app=1').strip()

def _missing_user_ids(ids: List[int]) -> List[int]:
    placeholders = ','.join('?' for _ in ids)
    with get_conn() as conn:
        rows = execute(conn, f'SELECT userid FROM users WHERE userid IN ({placeholders})', tuple(ids)).fetchall()
    present = {int(row[0]) for row in rows}
    return [uid for uid in ids if uid not in present]

def _validate_grant_template(template_name: str, language: str) -> None:
    """Fail before queuing if the approved template cannot render this notice."""
    template = _find_template(template_name, language)
    if not template:
        raise HTTPException(status_code=409, detail='Configured credit-grant WhatsApp template is not an approved Meta template')
    variables = _template_variables(template)
    body = [str(item.get('token') or '').strip().lower() for item in variables if item.get('component') == 'BODY']
    if body != ['1', '2'] or len(variables) != 2:
        raise HTTPException(status_code=409, detail='Credit-grant template must have exactly BODY {{1}} for credits added and {{2}} for new balance')
    buttons = [button for component in template.get('components') or []
               if str(component.get('type') or '').upper() == 'BUTTONS'
               for button in (component.get('buttons') or [])]
    chat_button = next((button for button in buttons
                        if str(button.get('type') or '').upper() == 'URL'
                        and str(button.get('text') or '').strip().lower() == 'chat now'), None)
    if not chat_button:
        raise HTTPException(status_code=409, detail='Credit-grant template needs a static URL button labelled “Chat Now”')
    url = str(chat_button.get('url') or '').strip()
    expected_url = _grant_chat_url()
    if not expected_url.startswith('https://'):
        raise HTTPException(status_code=500, detail='CREDIT_GRANT_WHATSAPP_CHAT_URL must be an HTTPS URL')
    if url != expected_url:
        raise HTTPException(status_code=409, detail='The “Chat Now” button URL does not match CREDIT_GRANT_WHATSAPP_CHAT_URL')

@router.get('/admin/campaigns/credit-grants')
async def list_grants(current_user: User = Depends(get_current_user)):
    _admin(current_user)
    return {'campaigns': await run_in_threadpool(list_credit_grant_campaigns), 'whatsapp_configured': _template_configured()}

@router.post('/admin/campaigns/credit-grants')
async def create_grant(body: GrantCreate, current_user: User = Depends(get_current_user)):
    _admin(current_user)
    ids = list(dict.fromkeys(int(uid) for uid in body.recipient_ids if int(uid) > 0))
    if not ids:
        raise HTTPException(status_code=400, detail='At least one valid user ID is required')
    missing = await run_in_threadpool(_missing_user_ids, ids)
    if missing:
        display = ', '.join(str(uid) for uid in missing[:20])
        suffix = ' …' if len(missing) > 20 else ''
        raise HTTPException(status_code=400, detail=f'Unknown user ID(s): {display}{suffix}. No credits were granted.')
    campaign = await run_in_threadpool(lambda: create_credit_grant_campaign(
        name=body.name, credits=body.credits, recipient_ids=ids, created_by=int(current_user.userid)))
    return {'campaign': campaign, 'whatsapp_configured': _template_configured()}

@router.post('/admin/campaigns/credit-grants/{campaign_id}/send-whatsapp')
async def send_grant_whatsapp(campaign_id: int, current_user: User = Depends(get_current_user)):
    _admin(current_user)
    template_name = (os.getenv('CREDIT_GRANT_WHATSAPP_TEMPLATE_NAME') or '').strip()
    language = (os.getenv('CREDIT_GRANT_WHATSAPP_TEMPLATE_LANGUAGE') or 'en').strip()
    if not template_name:
        raise HTTPException(status_code=409, detail='Set CREDIT_GRANT_WHATSAPP_TEMPLATE_NAME before sending WhatsApp notices')
    if not (os.getenv('WHATSAPP_NUDGE_PHONE_NUMBER_ID') or os.getenv('WHATSAPP_PHONE_NUMBER_ID')):
        raise HTTPException(status_code=409, detail='Set WHATSAPP_NUDGE_PHONE_NUMBER_ID (or WHATSAPP_PHONE_NUMBER_ID) before sending WhatsApp notices')
    await run_in_threadpool(_validate_grant_template, template_name, language)
    recipients = await run_in_threadpool(get_credit_grant_recipients_for_whatsapp, campaign_id)
    if not recipients:
        return {'queued': 0, 'detail': 'No credited recipients with an unqueued phone number'}
    batch_size = 25
    queued = 0
    for start in range(0, len(recipients), batch_size):
        batch = recipients[start:start + batch_size]
        task_id = f'credit-grant-{campaign_id}-{uuid.uuid4().hex}'
        if not enqueue_nudge_task(task_kind='credit-grant-whatsapp-batch', task_id=task_id,
                                  payload={'campaign_id': campaign_id, 'template_name': template_name,
                                           'language': language, 'recipients': batch}):
            raise HTTPException(status_code=503, detail='WhatsApp worker queue is unavailable; no notices were queued')
        await run_in_threadpool(mark_credit_grant_whatsapp_queued, campaign_id, [item['userid'] for item in batch])
        queued += len(batch)
    return {'queued': queued}
