"""Atomic, order-idempotent grants for verified Google Play purchases."""
from db import get_conn, execute


def grant_verified_order(*, userid, amount, order_id, metadata):
    if not order_id or amount <= 0:
        raise ValueError('Verified order ID and positive credits required')
    with get_conn() as conn:
        # Shared by API, RTDN and recovery tooling. Global order key also prevents
        # the same order being claimed by two different app accounts.
        execute(conn, 'SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', ('google_play:' + order_id,))
        existing = execute(conn, "SELECT userid, amount FROM credit_transactions WHERE source='google_play' AND reference_id=%s", (order_id,)).fetchone()
        if existing:
            if int(existing[0]) != int(userid) or int(existing[1]) != int(amount):
                raise ValueError('Verified order already belongs to a different account or amount')
            return {'credits_added': 0, 'already_credited': True}
        balance = execute(conn, '''
            INSERT INTO user_credits (userid, credits, updated_at) VALUES (%s,%s,CURRENT_TIMESTAMP)
            ON CONFLICT (userid) DO UPDATE SET credits=user_credits.credits+EXCLUDED.credits,
                updated_at=CURRENT_TIMESTAMP RETURNING credits
        ''', (userid, amount)).fetchone()[0]
        execute(conn, '''INSERT INTO credit_transactions
            (userid, transaction_type, amount, balance_after, source, reference_id, description, metadata)
            VALUES (%s,'earned',%s,%s,'google_play',%s,%s,%s)''',
            (userid, amount, balance, order_id, f'Google Play: credits_{amount}', metadata))
        conn.commit()
    return {'credits_added': amount, 'already_credited': False, 'balance_after': balance}
