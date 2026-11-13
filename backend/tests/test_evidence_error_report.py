import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from chat.evidence_error_report import query_filters, list_evidence_errors


def test_filter_validation_and_inclusive_ist_dates():
    base, final, params = query_filters('mismatches','A_%','2026-11-13','2026-11-13','speech')
    assert params == ['%A\\_\\%%', datetime(2026,11,12,18,30), datetime(2026,11,13,18,30), 'speech']
    assert 'mismatch_count > 0' in final
    for kwargs in [('other',None,None,None,None),('mismatches',None,'2026-02-30',None,None),('mismatches',None,'2026-11-14','2026-11-13',None)]:
        with pytest.raises(HTTPException): query_filters(*kwargs)


def test_evidence_errors_requires_admin():
    from chat_history.admin_routes import router,require_admin
    route=next(r for r in router.routes if r.path=='/admin/chat/evidence-errors')
    assert any(d.call is require_admin for d in route.dependant.dependencies)
    with pytest.raises(HTTPException): require_admin(SimpleNamespace(role='user'))


@pytest.fixture
def db_conn():
    from dotenv import load_dotenv
    import psycopg2
    from psycopg2.extensions import parse_dsn
    from db import _postgres_dsn
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    dsn=_postgres_dsn()
    if parse_dsn(dsn).get('host') not in ('/tmp','localhost','127.0.0.1'):pytest.skip('Local-only temporary database tests')
    conn=psycopg2.connect(dsn)
    try:
        with conn.cursor() as c:
            c.execute('CREATE TEMP TABLE users (userid int, name text) ON COMMIT DROP')
            c.execute('CREATE TEMP TABLE chat_sessions (session_id text, user_id int) ON COMMIT DROP')
            c.execute('CREATE TEMP TABLE chat_messages (message_id int, session_id text, timestamp timestamp, chat_tier text) ON COMMIT DROP')
            c.execute('CREATE TEMP TABLE chat_answer_evidence_audits (message_id int,status text,error_message text,created_at timestamp,evidence_brief text,evaluator_result text) ON COMMIT DROP')
            c.execute("INSERT INTO users VALUES (1,'Alice'),(2,'Bob'); INSERT INTO chat_sessions VALUES ('s1',1),('s2',2)")
            fixtures=[(1,'completed',['mismatch'],'standard','s1','2026-11-12 18:30'),
                      (2,'completed',['unsupported'],'instant','s1','2026-11-13 10:00'),
                      (3,'failed',[],'speech','s2','2026-11-13 11:00'),
                      (4,'completed',['match'],'premium','s2','2026-11-13 12:00'),
                      (5,'completed',['mismatch','ambiguous'],'verified','s2','2026-11-13 18:29:59'),
                      (6,'completed',['mismatch'],'speech','s1','2026-11-13 18:30'),
                      (7,'completed',[],'standard','s1','2026-11-13 13:00')]
            for mid,status,findings,tier,session,date in fixtures:
                c.execute('INSERT INTO chat_messages VALUES (%s,%s,%s,%s)',(mid,session,date,tier))
                report={'fact_checks':[{'status':f} for f in findings], 'counts':{'mismatch':999},'claim_checks':[{'status':'conflicts'}]}
                c.execute('INSERT INTO chat_answer_evidence_audits VALUES (%s,%s,%s,%s,%s,%s)',(mid,status,'provider timeout' if status=='failed' else None,date,json.dumps({'question':f'Question {mid}','chat_tier':tier}),json.dumps(report)))
        yield conn
    finally:
        conn.rollback();conn.close()


def test_database_classification_filters_pagination_and_boundary(db_conn):
    result=list_evidence_errors(db_conn,start_date='2026-11-13',end_date='2026-11-13',limit=1)
    assert result['total']==2 and result['total_pages']==2
    assert result['items'][0]['message_id']==5
    assert result['items'][0]['question']=='Question 5'
    second=list_evidence_errors(db_conn,start_date='2026-11-13',end_date='2026-11-13',limit=1,page=2)
    assert second['items'][0]['message_id']==1
    assert second['items'][0]['answer_at'].startswith('2026-11-13T00:00:00')
    assert list_evidence_errors(db_conn,username='alice',chat_type='speech')['items'][0]['message_id']==6
    assert list_evidence_errors(db_conn,username='Alice',chat_type='verified')['total']==0
    assert {r['message_id'] for r in list_evidence_errors(db_conn,view='unverified')['items']}=={2,5}
    assert {r['message_id'] for r in list_evidence_errors(db_conn,view='failures')['items']}=={3}
    assert list_evidence_errors(db_conn,view='failures')['items'][0]['error_message']=='provider timeout'
