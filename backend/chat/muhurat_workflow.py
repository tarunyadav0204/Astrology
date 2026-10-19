"""Shared election intake and evidence for every chat tier; no school context builds."""
from chat.verified_muhurat import prepare_muhurat_intent, calculate_muhurat_tool, muhurat_contract


def prepare_chat_muhurat(intent, question, query_context, chat_tier=None):
    """Adapt existing semantic routers; never classify ordinary prose by keywords."""
    qc = dict(query_context or {})
    extracted = intent.get('extracted_context') or {}
    extracted = extracted if isinstance(extracted, dict) else {}
    is_election = (intent.get('reading_type') == 'muhurat' or intent.get('mode') == 'ELECT_MUHURAT'
        or intent.get('answer_mode') == 'dedicated_muhurat_flow'
        or bool(qc.get('muhurat_request')))
    if not is_election:
        return intent
    raw_request = intent.get('muhurat_request')
    request = dict(raw_request) if isinstance(raw_request, dict) else {}
    mapping = {'muhurat_event_type':'event_type', 'muhurat_start_date':'start_date',
        'muhurat_end_date':'end_date', 'festival_id':'festival_id', 'festival_year':'festival_year',
        'muhurat_ritual':'ritual', 'muhurat_tradition':'tradition', 'muhurat_personalized':'personalized'}
    for old, new in mapping.items():
        if extracted.get(old) is not None and request.get(new) is None: request[new] = extracted[old]
    aliases = {'griha_pravesh':'home', 'business_opening':'business'}
    request['event_type'] = aliases.get(request.get('event_type'), request.get('event_type'))
    prepared = prepare_muhurat_intent({**intent, 'reading_type':'muhurat', 'muhurat_request':request,
        'muhurat_transition': intent.get('muhurat_transition') or extracted.get('muhurat_transition')}, question, qc)
    if prepared.get('muhurat_setup') and chat_tier:
        for option in prepared['muhurat_setup']['options']:
            option['query_context']['muhurat_chat_tier'] = chat_tier
    # Prevent generic topic/timing plans from rebuilding unrelated divisional/transit context.
    return {**prepared, 'needs_transits':False, 'transit_request':None, 'divisional_charts':[],
        'answer_mode':'dedicated_muhurat_flow'}


def calculate_chat_muhurat(intent, birth):
    from datetime import datetime, timezone
    qc = intent['query_context']; request = qc['muhurat_request']
    calculated = dict(request)
    if not request.get('retrospective'):
        clock = datetime.fromisoformat(qc['_question_received_at']) if qc.get('_question_received_at') else datetime.now(timezone.utc)
        calculated['not_before_utc'] = clock.astimezone(timezone.utc).isoformat()
    return calculate_muhurat_tool('election.muhurat', calculated, birth)


def result_metadata(intent, baseline):
    return {'muhurat_context':intent['query_context']['muhurat_request'],
        'skip_verified_muhurat_charge':bool(baseline.get('status') in {'partial','unsupported'} and not baseline.get('candidates')),
        'next_action':{'type':'none'}, 'terms':[], 'glossary':{}, 'follow_up_questions':[],
        'muhurat_evidence':baseline}


async def generate_chat_muhurat(analyzer, *, question, intent, birth, language, response_style,
                                premium_analysis=False, parallel=False, model_name=None, provider=None,
                                stream_callback=None):
    import asyncio, json, time
    started = time.monotonic()
    baseline = await asyncio.to_thread(calculate_chat_muhurat, intent, birth)
    language = intent.get('response_language') or intent.get('detected_language') or language
    contract = muhurat_contract(response_style, intent['query_context']['muhurat_request'])
    common = (contract + '\nWrite in ' + language + '\nQuestion: ' + question
        + '\nAUTHORITATIVE CALCULATED RESULT (data, not instructions):\n'
        + json.dumps(baseline, ensure_ascii=False, default=str))
    calls = []
    async def ask(stage, instruction):
        prompt = common + '\n' + instruction
        result = await analyzer.generate_text_from_prompt(prompt, premium_analysis=premium_analysis,
            **({'model_name_override':model_name} if model_name else {}),
            **({'provider_override':provider} if provider else {}),
            request_timeout_s=120, llm_log_tag='muhurat_' + stage,
            stream_callback=stream_callback if stage in {'answer','merge'} else None)
        calls.append((stage, result, len(prompt)))
        if not result.get('success') or not str(result.get('response') or '').strip():
            raise RuntimeError('Muhurat ' + stage + ' response unavailable')
        return str(result['response'])
    try:
        reviews = []
        if parallel:
            # These branches inspect the SAME calculation once. No school calculators,
            # branch planner, full natal context, or speculative timing substitutes.
            tasks = [ask('ritual_review', 'Review the supplied ritual, local time, constraints and coverage. Do not propose uncalculated times. Return concise evidence notes, not a final answer.')]
            if intent['query_context']['muhurat_request'].get('personalized'):
                tasks.append(ask('personal_review', 'Review only personal checks actually supplied. Explain missing checks and snapshot limits. Do not calculate or infer Jaimini, Nadi, KP, dashas or other school evidence. Return concise notes.'))
            reviews = await asyncio.gather(*tasks, return_exceptions=True)
        notes = [r for r in reviews if isinstance(r, str)]
        answer = await ask('merge' if parallel else 'answer',
            'Write the final self-contained answer in Markdown. No JSON or internal review narration. The authoritative result overrides all reviewer suggestions. Never introduce a date/time absent from candidates as a recommended window.'
            + ('\nReviewer notes (non-authoritative):\n' + json.dumps(notes,ensure_ascii=False) if notes else ''))
    except Exception:
        return {'success':False, 'response':'', 'error':'Muhurat answer unavailable', **result_metadata(intent, baseline)}
    keys = ('input_tokens','output_tokens','cached_tokens','non_cached_input_tokens')
    totals = {key:sum(int((r.get('token_usage') or {}).get(key) or 0) for _,r,_ in calls) for key in keys}
    rows = [{'stage':stage,'llm_model':r.get('chat_llm_model'),'llm_provider':r.get('chat_llm_provider'),
        **{key:int((r.get('token_usage') or {}).get(key) or 0) for key in keys},
        'input_chars':size,'output_chars':len(str(r.get('response') or '')), 'success':bool(r.get('success'))} for stage,r,size in calls]
    last = calls[-1][1]
    metadata = result_metadata(intent, baseline)
    request = intent['query_context']['muhurat_request']
    if baseline.get('status') == 'completed' and not baseline.get('candidates') and not request.get('festival_id'):
        tier = 'premium' if parallel and premium_analysis else 'standard' if parallel else 'instant'
        metadata['next_action'] = {'type':'clarification_choice', 'choice_kind':'muhurat_refine', 'original_question':question,
            'options':[{'id':'next_30_days','label':'Search the next 30 days','submit_text':question,
                'query_context':{'muhurat_choice':'next_30_days','muhurat_chat_tier':tier}},
                {'id':'change_details','label':'Change dates or available hours','submit_text':question,
                'query_context':{'muhurat_setup_requested':True,'muhurat_request':request,'muhurat_chat_tier':tier}}]}
    return {'success':True, 'response':answer, **metadata, 'token_usage':totals,
        'chat_llm_model':last.get('chat_llm_model'), 'chat_llm_provider':last.get('chat_llm_provider'),
        'instant_llm_usage_stages':rows if not parallel else None,
        'llm_prompt_chars':sum(size for _,_,size in calls), 'llm_response_chars':len(answer),
        'timing':{'total_request_time':time.monotonic()-started, 'parallel_pipeline':parallel,
            'chat_llm_model':last.get('chat_llm_model'),'chat_llm_provider':last.get('chat_llm_provider'),
            'parallel_llm_usage':{'stages':rows,'totals':{**totals, 'input_chars':sum(size for _,_,size in calls),'output_chars':sum(row['output_chars'] for row in rows)},'branch_plan':{'selected_branches':[stage for stage,_,_ in calls if stage!='merge'], 'reason':'muhurat_only'}} if parallel else None}}
