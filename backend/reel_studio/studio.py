"""Curated chart readings that enter the existing charged reel pipeline."""
import hashlib
import json
from reel_studio import planner
import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from auth import get_current_user
from db import execute, get_conn
from reel_studio.billing import reel_pricing
from reel_studio import costs
from reel_studio.topic_evidence import EVIDENCE_VERSION, build_topic_evidence

router = APIRouter(prefix='/reel-studio', tags=['reel-studio'])
# Existing chat IDs are positive and chapter IDs occupy the small negative range.
# Reserve a disjoint INTEGER range so saved reels keep their existing identifiers.
SOURCE_OFFSET = 1_000_000_000
TOPICS = {
    'know_me': ('Before You Say You Know Me', 'Explain my nature and behaviour to my partner: the difference between what I show and what I feel, how I communicate, what I need when stressed, and practical ways to understand me. Do not assume I currently have a partner.'),
    'love_me': ('How to Love Me Better', 'Explain what helps me feel loved, supported and emotionally safe, how I express affection, what may create misunderstandings, and practical ways a partner can connect with me. Do not assume relationship status.'),
    'real_me': ('First Impression vs. the Real Me', 'Contrast the first impression I may give with my inner emotional needs and behaviour once I trust someone. Give concrete, relatable situations and a nuanced picture rather than flattering stereotypes.'),
    'superpower': ('My Hidden Superpower', 'Identify my most meaningful underused strengths, how these can show up in everyday situations, their possible blind spots, and one practical way to develop each strength. Avoid generic praise.'),
    'career': ('My Career Sweet Spot', 'Explain the kinds of tasks, roles, working styles and environments that may fit my chart. Give concrete examples and trade-offs. Do not promise career success, income or specific job outcomes.'),
}


def schema(conn):
    execute(conn, '''CREATE TABLE IF NOT EXISTS reel_studio_sources (
        id SERIAL PRIMARY KEY CHECK (id < 1000000000), user_id INTEGER NOT NULL,
        chart_id INTEGER NOT NULL, topic TEXT NOT NULL, fingerprint TEXT NOT NULL,
        reading_json TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id,chart_id,topic,fingerprint))''')


def fingerprint(birth):
    return hashlib.sha256(json.dumps(birth, sort_keys=True, default=str).encode()).hexdigest()


@router.get('/catalog')
def catalog(user=Depends(get_current_user)):
    from next_chapter.customer import price
    chapter_cost, _ = price(user.userid)
    return {'topics': list(TOPICS) + ['next_chapter'], 'pricing': reel_pricing(user.userid),
            'chapter_credit_cost': chapter_cost}


class SourceRequest(BaseModel):
    birth_chart_id: int = Field(gt=0)
    topic: Literal['know_me', 'love_me', 'real_me', 'superpower', 'career']


@router.post('/sources')
def create_source(payload: SourceRequest, user=Depends(get_current_user)):
    from next_chapter.customer import owned_birth
    birth = owned_birth(payload.birth_chart_id, user.userid)
    with get_conn() as conn:
        schema(conn)
        row = execute(conn, '''INSERT INTO reel_studio_sources(user_id,chart_id,topic,fingerprint)
            VALUES (%s,%s,%s,%s) ON CONFLICT(user_id,chart_id,topic,fingerprint)
            DO UPDATE SET topic=EXCLUDED.topic RETURNING id''',
            (user.userid, payload.birth_chart_id, payload.topic, fingerprint(birth))).fetchone()
        conn.commit()
    # No model calls or debits until the user confirms the existing reel setup.
    return {'message_id': -(SOURCE_OFFSET + row[0])}


def answer_for_source(message_id, user_id):
    from next_chapter.customer import owned_birth
    with get_conn() as conn:
        row = execute(conn, '''SELECT chart_id,topic,fingerprint,reading_json FROM reel_studio_sources
            WHERE id=%s AND user_id=%s''', (-message_id-SOURCE_OFFSET, user_id)).fetchone()
    if not row:
        raise HTTPException(404, 'Reel source not found')
    chart_id, topic, expected, saved = row
    birth = owned_birth(chart_id, user_id)
    if fingerprint(birth) != expected:
        raise HTTPException(409, 'The chart has changed. Please reopen Reel Studio and select this topic again.')
    title, brief = TOPICS[topic]
    if saved and json.loads(saved).get('evidence_version') == EVIDENCE_VERSION:
        return saved, chart_id, brief
    evidence = build_topic_evidence(birth, topic)
    prompt = f'''Write a thoughtful personal astrology reading for a shareable AstroRoshni reel.
TOPIC: {title}
QUESTION: {brief}
Use only the supplied topic-specific calculated evidence. This is an interpretation, not a diagnosis or a certainty.
You are the narrator, not the astrology calculator. House verdicts, support/pressure, dignity,
Shadbala, combustion, star/pada/dispositor conditions, D9/D10 and Jaimini/Nadi relationships
have already been calculated. Do not calculate new aspects, assign strengths from raw numbers,
infer new yogas, or replace a mixed worksheet verdict with an unqualified positive claim.
Weigh the supplied support AND pressure together; distinguish D1 findings from D9/D10 corroboration.
Use relevant Jaimini and Nadi findings where they add specific insight, without forcing every
system into every paragraph. Follow the packet's conventions. Tied karakas are uncertain.
Connect calculated findings into concrete topic-relevant everyday examples; examples are
possibilities, not facts about the person's life. Do not default every topic to money/career.
For first impressions contrast calculated Arudha evidence with Lagna/Moon and inner conditions;
for relationships explain communication, emotional needs and trust without predicting a spouse;
for strengths/career explain tasks and environments with both enabling and limiting evidence.
Never call Nadi virtual positions actual placements or its trine links node graha aspects.
Do not claim all evidence agrees when it does not.
Write a conversational explanation addressing this exact topic, using second person, concrete everyday examples, balanced strengths and challenges, and useful guidance. Aim for 600–850 words only when the evidence needs that detail; never pad to reach a length. Use direct, spoken sentences rather than a formal report or repeated "your chart indicates" lead-ins. Preserve uncertainty and explain technical terms simply.
Explain why with a few specific verified placements. Never invent degrees, aspects, dignity, divisional placements or timing.
Do not assume marriage, children, gender, occupation or other life circumstances not supplied. Phrase those conditionally.
Do not expose birth details, identifiers or names. Do not give medical diagnoses, deterministic labels, frightening predictions or relationship ultimatums.
Do not add a greeting, sales pitch, markdown table or repeated closing. Avoid generic flattery.
Return JSON with a title and reading, both strings, in English; the reel planner will faithfully translate to the user's chosen language.
CALCULATED TOPIC EVIDENCE: {json.dumps(evidence, ensure_ascii=False, default=str)}'''
    response = planner.create('studio_reading', input=prompt, store=False, max_output_tokens=3500,
        text={'format': {'type': 'json_schema', 'name': 'studio_reading', 'strict': True,
            'schema': {'type':'object','properties':{'title':{'type':'string'},'reading':{'type':'string'}},
                       'required':['title','reading'],'additionalProperties':False}}})
    reading = json.loads(response.output_text)
    if not str(reading.get('reading') or '').strip():
        raise HTTPException(503, 'Could not prepare this reading. No credits were charged.')
    # Keep the exact calculated packet with the reading for audit and subsequent
    # storyboard grounding. Older generic snapshots are not reused on regeneration.
    reading['evidence_version'] = EVIDENCE_VERSION
    reading['calculated_evidence'] = evidence
    value = json.dumps(reading, ensure_ascii=False, default=str)
    with get_conn() as conn:
        execute(conn, 'UPDATE reel_studio_sources SET reading_json=%s WHERE id=%s AND user_id=%s',
                (value, -message_id-SOURCE_OFFSET, user_id))
        conn.commit()
    return value, chart_id, brief
