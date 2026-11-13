"""Exercise real PostgreSQL transactions in an isolated local test schema."""
import os,sys,uuid
from pathlib import Path
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import pytest
import psycopg2
from psycopg2.extensions import parse_dsn
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from credits import play_credit_grant as grant

@pytest.fixture
def ledger(monkeypatch):
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    dsn=os.getenv('POSTGRES_DSN') or os.getenv('DATABASE_URL')
    if not dsn or parse_dsn(dsn).get('host','') not in ('','/tmp','localhost','127.0.0.1'):
        pytest.skip('Requires local PostgreSQL')
    schema='test_play_'+uuid.uuid4().hex
    admin=psycopg2.connect(dsn);admin.autocommit=True
    with admin.cursor() as cur:
        cur.execute(f'CREATE SCHEMA {schema}')
        cur.execute(f'CREATE TABLE {schema}.user_credits(userid bigint PRIMARY KEY,credits int NOT NULL,updated_at timestamp)')
        cur.execute(f'''CREATE TABLE {schema}.credit_transactions(userid bigint,transaction_type text,amount int,
            balance_after int,source text,reference_id text UNIQUE,description text,metadata text CHECK(metadata <> 'fail'))''')
    @contextmanager
    def connect():
        c=psycopg2.connect(dsn,options=f'-c search_path={schema}')
        try:yield c
        finally:c.rollback();c.close()
    monkeypatch.setattr(grant,'get_conn',connect)
    yield connect
    with admin.cursor() as cur:cur.execute(f'DROP SCHEMA {schema} CASCADE')
    admin.close()

def call(order,userid=1,metadata='{}'):
    return grant.grant_verified_order(userid=userid,amount=24,order_id=order,metadata=metadata)

def test_concurrent_replays_credit_exactly_once(ledger):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:call('GPA.same'),range(12)))
    assert sum(r['credits_added'] for r in results)==24
    with ledger() as c:
        cur=c.cursor();cur.execute('SELECT credits FROM user_credits');assert cur.fetchone()[0]==24
        cur.execute('SELECT count(*) FROM credit_transactions');assert cur.fetchone()[0]==1

def test_concurrent_distinct_orders_keep_all_credits(ledger):
    with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(lambda i:call(f'GPA.{i}'),range(12)))
    with ledger() as c:
        cur=c.cursor();cur.execute('SELECT credits FROM user_credits');assert cur.fetchone()[0]==288

def test_foreign_owner_and_failed_insert_leave_balance_unchanged(ledger):
    call('GPA.original')
    with pytest.raises(ValueError):call('GPA.original',userid=2)
    with pytest.raises(psycopg2.IntegrityError):call('GPA.failure',metadata='fail')
    with ledger() as c:
        cur=c.cursor();cur.execute('SELECT userid,credits FROM user_credits');assert cur.fetchall()==[(1,24)]
