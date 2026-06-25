import json
import logging
import os
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any

# Sentinel: pass this as discount to mean "do not change discount column"
_DISCOUNT_OMIT = object()
logger = logging.getLogger(__name__)


class CreditService:
    def __init__(self):
        if self._should_init_tables_on_startup():
            self.init_tables()

    @staticmethod
    def _should_init_tables_on_startup() -> bool:
        return (os.getenv("CREDIT_SERVICE_INIT_ON_STARTUP") or "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def _date_today_expr(self) -> str:
        return "CURRENT_DATE"

    @staticmethod
    def _safe_ddl(conn, sql: str) -> None:
        """Run DDL on Postgres; rollback on failure so the connection stays usable."""
        from db import execute

        try:
            execute(conn, sql)
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

    def _date_yesterday_expr(self) -> str:
        return "CURRENT_DATE - INTERVAL '1 day'"

    def _upsert_user_credits(self, conn, userid: int, credits: int, free_used: Optional[int] = None) -> None:
        """
        Upsert user_credits row. Keeps SQLite and Postgres behavior aligned.
        """
        from db import execute

        try:
            if free_used is None:
                execute(
                    conn,
                    """
                    INSERT INTO user_credits (userid, credits, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT (userid) DO UPDATE
                      SET credits = EXCLUDED.credits,
                          updated_at = CURRENT_TIMESTAMP
                    """,
                    (userid, credits),
                )
            else:
                execute(
                    conn,
                    """
                    INSERT INTO user_credits (userid, credits, free_chat_question_used, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT (userid) DO UPDATE
                      SET credits = EXCLUDED.credits,
                          free_chat_question_used = GREATEST(user_credits.free_chat_question_used, EXCLUDED.free_chat_question_used),
                          updated_at = CURRENT_TIMESTAMP
                    """,
                    (userid, credits, int(free_used)),
                )
        except Exception as e:
            # Postgres requires a UNIQUE/exclusion constraint for ON CONFLICT (userid).
            # If user_credits.userid is missing that constraint (partial migration),
            # we must not crash the whole purchase; fall back to manual UPDATE-then-INSERT.
            msg = str(e)
            if "ON CONFLICT" not in msg or "specification" not in msg:
                raise

            if free_used is None:
                cur = execute(
                    conn,
                    "UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
                    (credits, userid),
                )
                if getattr(cur, "rowcount", 0) == 0:
                    execute(
                        conn,
                        "INSERT INTO user_credits (userid, credits, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                        (userid, credits),
                    )
            else:
                free_int = int(free_used)
                cur = execute(
                    conn,
                    """
                    UPDATE user_credits
                    SET credits = ?,
                        free_chat_question_used = GREATEST(free_chat_question_used, ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE userid = ?
                    """,
                    (credits, free_int, userid),
                )
                if getattr(cur, "rowcount", 0) == 0:
                    execute(
                        conn,
                        """
                        INSERT INTO user_credits (userid, credits, free_chat_question_used, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (userid, credits, free_int),
                    )
    
    def init_tables(self):
        """Initialize credit-related tables"""
        from db import get_conn, execute

        with get_conn() as conn:
            cursor = conn.cursor()
        
        # User credits table
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS user_credits (
                    id SERIAL PRIMARY KEY,
                    userid INTEGER NOT NULL UNIQUE,
                    credits INTEGER DEFAULT 0,
                    free_chat_question_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Best-effort: ensure ON CONFLICT (userid) can work in partially-migrated DBs.
            # If schema exists without the UNIQUE constraint on userid, this creates it.
            # If duplicates already exist, the CREATE UNIQUE INDEX will fail; manual upsert fallback
            # in _upsert_user_credits will still keep the app functional.
            try:
                execute(
                    conn,
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_credits_userid_unique ON user_credits(userid)",
                )
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

            # Web: honor-system flag when browser notification permission is granted (free-first-question gate).
            self._safe_ddl(
                conn,
                "ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS web_notifications_granted INTEGER DEFAULT 0",
            )

            # Global guardrail: one free standard-chat question per normalized birth hash
            # across all accounts (prevents multi-account abuse on same chart data).
            execute(
                conn,
                '''
                CREATE TABLE IF NOT EXISTS free_chat_birth_hash_usage (
                    id BIGSERIAL PRIMARY KEY,
                    birth_hash TEXT NOT NULL UNIQUE,
                    first_userid INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )

            self._safe_ddl(conn, "ALTER TABLE birth_charts ADD COLUMN IF NOT EXISTS birth_hash TEXT")
            self._safe_ddl(
                conn,
                "CREATE INDEX IF NOT EXISTS idx_birth_charts_policy_hash ON birth_charts (birth_hash)",
            )

        # Credit transactions table
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS credit_transactions (
                    id SERIAL PRIMARY KEY,
                    userid INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    reference_id TEXT,
                    description TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS promo_codes (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    credits INTEGER NOT NULL,
                    max_uses INTEGER DEFAULT 1,
                    max_uses_per_user INTEGER DEFAULT 1,
                    used_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    expires_at TIMESTAMP,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS promo_code_usage (
                    id SERIAL PRIMARY KEY,
                    promo_code_id INTEGER NOT NULL,
                    userid INTEGER NOT NULL,
                    credits_earned INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS credit_settings (
                    id SERIAL PRIMARY KEY,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value INTEGER NOT NULL,
                    description TEXT,
                    discount INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # RTDN idempotency log: one row per processed Google Play subscription event.
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS play_subscription_event_log (
                    id BIGSERIAL PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    purchase_token TEXT,
                    product_id TEXT,
                    notification_type INTEGER,
                    event_time_millis BIGINT,
                    payload_json TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            for col_def in (
                "userid INTEGER",
                "source TEXT",
                "event_kind TEXT",
                "start_date DATE",
                "end_date DATE",
                "google_play_order_id TEXT",
                "order_id_base TEXT",
            ):
                self._safe_ddl(
                    conn,
                    f"ALTER TABLE play_subscription_event_log ADD COLUMN IF NOT EXISTS {col_def}",
                )

            execute(conn, '''
                CREATE TABLE IF NOT EXISTS play_subscription_token_map (
                    id BIGSERIAL PRIMARY KEY,
                    userid INTEGER NOT NULL,
                    purchase_token TEXT NOT NULL UNIQUE,
                    product_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self._safe_ddl(conn, "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS google_play_order_id TEXT")
            self._safe_ddl(conn, "ALTER TABLE play_subscription_token_map ADD COLUMN IF NOT EXISTS latest_order_id TEXT")
            self._safe_ddl(conn, "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS razorpay_plan_id TEXT")
            for col_def in (
                "billing_provider TEXT",
                "razorpay_subscription_id TEXT",
                "cancel_at_period_end BOOLEAN DEFAULT FALSE",
            ):
                self._safe_ddl(
                    conn,
                    f"ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS {col_def}",
                )

            execute(conn, '''
                CREATE TABLE IF NOT EXISTS razorpay_subscription_map (
                    razorpay_subscription_id TEXT PRIMARY KEY,
                    userid INTEGER NOT NULL,
                    internal_plan_id INTEGER,
                    product_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            execute(conn, '''
                CREATE TABLE IF NOT EXISTS play_onetime_token_map (
                    id BIGSERIAL PRIMARY KEY,
                    userid INTEGER NOT NULL,
                    purchase_token TEXT NOT NULL UNIQUE,
                    product_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # RTDN idempotency log for one-time product purchase events.
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS play_onetime_event_log (
                    id BIGSERIAL PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    purchase_token TEXT,
                    product_id TEXT,
                    notification_type INTEGER,
                    event_time_millis BIGINT,
                    payload_json TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Durable backlog for one-time RTDN events whose purchase token is not yet
            # mapped to an app user at the time Google notifies us.
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS play_onetime_pending_event (
                    id BIGSERIAL PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    purchase_token TEXT NOT NULL,
                    product_id TEXT,
                    notification_type INTEGER,
                    event_time_millis BIGINT,
                    payload_json TEXT,
                    userid INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending',
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_retry_at TIMESTAMP,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    resolved_at TIMESTAMP,
                    resolution_note TEXT,
                    last_error TEXT
                )
            ''')

            # Hard guard against double-credit race conditions for Google Play credits.
            # PostgreSQL supports partial unique indexes with IF NOT EXISTS.
            try:
                execute(
                    conn,
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_tx_gp_unique_ref
                    ON credit_transactions(userid, source, reference_id)
                    WHERE source = 'google_play' AND reference_id IS NOT NULL
                    """,
                )
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

            # Hard guard against giving the first-purchase bonus more than once per user.
            try:
                execute(
                    conn,
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_tx_first_purchase_bonus_once
                    ON credit_transactions(userid, source)
                    WHERE source = 'first_purchase_bonus'
                    """,
                )
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

            try:
                execute(
                    conn,
                    """
                    CREATE INDEX IF NOT EXISTS idx_credit_tx_created_at
                    ON credit_transactions(created_at DESC)
                    """,
                )
                execute(
                    conn,
                    """
                    CREATE INDEX IF NOT EXISTS idx_credit_tx_source_type_created
                    ON credit_transactions(source, transaction_type, created_at DESC)
                    """,
                )
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

            # Backfill: users who have ever paid for a chat question should not get "first question free"
            try:
                execute(conn, """
                    UPDATE user_credits SET free_chat_question_used = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE userid IN (
                        SELECT DISTINCT userid FROM credit_transactions
                        WHERE source = 'feature_usage' AND reference_id = 'chat_question'
                    )
                """)
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

            # Insert default credit costs
            defaults = [
                ("chat_question_cost", 1, "Credits per chat question"),
                ("instant_chat_cost", 1, "Credits per instant chat answer"),
                ("speech_chat_cost", 1, "Credits per speech chat turn (Tara / voice-first)"),
                ("wealth_analysis_cost", 5, "Credits per wealth analysis"),
                ("marriage_analysis_cost", 3, "Credits per marriage analysis"),
                ("health_analysis_cost", 3, "Credits per health analysis"),
                ("education_analysis_cost", 3, "Credits per education analysis"),
                ("premium_chat_cost", 10, "Credits per premium deep analysis chat"),
                ("career_analysis_cost", 12, "Credits per career analysis"),
                ("progeny_analysis_cost", 15, "Credits per progeny analysis"),
                ("trading_daily_cost", 5, "Credits per daily trading forecast"),
                ("trading_monthly_cost", 20, "Credits per monthly trading calendar"),
                ("childbirth_planner_cost", 8, "Credits per childbirth muhurat planning"),
                ("vehicle_purchase_cost", 10, "Credits per vehicle purchase muhurat"),
                ("griha_pravesh_cost", 15, "Credits per griha pravesh muhurat"),
                ("gold_purchase_cost", 12, "Credits per gold purchase muhurat"),
                ("business_opening_cost", 20, "Credits per business opening muhurat"),
                ("event_timeline_cost", 100, "Credits per yearly event timeline analysis"),
                ("partnership_analysis_cost", 2, "Credits per partnership compatibility analysis"),
                ("karma_analysis_cost", 25, "Credits per karma analysis"),
                ("ashtakavarga_life_predictions_cost", 15, "Credits per Ashtakavarga life predictions (Dots of Destiny)"),
                ("podcast_cost", 2, "Credits per podcast (listen to message as audio)"),
            ]
            for key, value, desc in defaults:
                cur = execute(conn, "SELECT COUNT(*) FROM credit_settings WHERE setting_key = ?", (key,))
                if cur.fetchone()[0] == 0:
                    execute(
                        conn,
                        "INSERT INTO credit_settings (setting_key, setting_value, description) VALUES (?, ?, ?)",
                        (key, int(value), desc),
                    )

            conn.commit()
            return
    
    def get_user_credits(self, userid: int) -> int:
        """Get current credit balance for user"""
        from db import get_conn, execute
        with get_conn() as conn:
            cursor = execute(conn, "SELECT credits FROM user_credits WHERE userid = ?", (userid,))
            result = cursor.fetchone()
            return int(result[0]) if result and result[0] is not None else 0

    def get_subscription_discount_percent(self, userid: int) -> int:
        """Return 0-100 discount percent for user's active subscription tier. 0 if no plan or column missing (backward compat)."""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                date_expr = self._date_today_expr()
                cursor = execute(conn, f"""
                    SELECT COALESCE(sp.discount_percent, 0)
                    FROM user_subscriptions us
                    JOIN subscription_plans sp ON us.plan_id = sp.plan_id
                    WHERE us.userid = ? AND us.status = 'active' AND us.end_date >= {date_expr}
                    ORDER BY sp.discount_percent DESC
                    LIMIT 1
                """, (userid,))
                row = cursor.fetchone()
        except Exception:
            row = None
        if not row:
            return 0
        return max(0, min(100, int(row[0]) if row[0] is not None else 0))

    def get_subscription_tier_name(self, userid: int) -> Optional[str]:
        """Return tier display name for user's active subscription, or None. Backward compat: returns None if tables/columns missing."""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                date_expr = self._date_today_expr()
                cursor = execute(conn, f"""
                    SELECT sp.tier_name
                    FROM user_subscriptions us
                    JOIN subscription_plans sp ON us.plan_id = sp.plan_id
                    WHERE us.userid = ? AND us.status = 'active' AND us.end_date >= {date_expr}
                    ORDER BY sp.discount_percent DESC
                    LIMIT 1
                """, (userid,))
                row = cursor.fetchone()
        except Exception:
            row = None
        return (row[0] if row and row[0] else None) or None

    def get_user_subscription_details(self, userid: int) -> Optional[dict]:
        """Return full details of user's active subscription: tier_name, discount_percent, start_date, end_date, features. None if no active subscription."""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                date_expr = self._date_today_expr()
                cursor = execute(conn, f"""
                    SELECT sp.tier_name, sp.discount_percent, us.start_date, us.end_date, sp.features,
                           us.billing_provider, us.razorpay_subscription_id, us.cancel_at_period_end,
                           sp.plan_id, sp.price, sp.google_play_product_id
                    FROM user_subscriptions us
                    JOIN subscription_plans sp ON us.plan_id = sp.plan_id
                    WHERE us.userid = ? AND us.status = 'active' AND us.end_date >= {date_expr}
                    ORDER BY sp.discount_percent DESC
                    LIMIT 1
                """, (userid,))
                row = cursor.fetchone()
        except Exception:
            row = None
        if not row:
            return None
        features = row[4]
        billing_provider = (row[5] or "").strip().lower() or None
        razorpay_sub_id = (row[6] or "").strip() or None
        cancel_at_period_end = bool(row[7]) if row[7] is not None else False
        internal_plan_id = row[8]
        plan_price = float(row[9]) if row[9] is not None else None
        google_product_id = row[10]
        if not billing_provider:
            billing_provider = "razorpay" if razorpay_sub_id else "google_play"
        if isinstance(features, str):
            try:
                features = json.loads(features) if features else {}
            except (ValueError, TypeError):
                features = {}
        return {
            "tier_name": row[0] or "VIP",
            "discount_percent": max(0, min(100, int(row[1]) if row[1] is not None else 0)),
            "start_date": row[2] or "",
            "end_date": row[3] or "",
            "features": features,
            "billing_provider": billing_provider,
            "razorpay_subscription_id": razorpay_sub_id,
            "cancel_at_period_end": cancel_at_period_end,
            "plan_id": internal_plan_id,
            "plan_price_inr": plan_price,
            "google_play_product_id": google_product_id,
            "manage_in_google_play": billing_provider == "google_play",
            "manage_on_web": billing_provider == "razorpay",
        }

    def get_plan_id_by_google_play_product_id(self, product_id: str, platform: str = "astroroshni") -> Optional[int]:
        """Return plan_id for subscription_plans where google_play_product_id = product_id. None if not found."""
        from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE
        try:
            with get_conn() as conn:
                cursor = execute(
                    conn,
                    f"SELECT plan_id FROM subscription_plans WHERE google_play_product_id = %s AND platform = %s AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}",
                    (product_id.strip(), platform),
                )
                row = cursor.fetchone()
        except Exception:
            row = None
        return row[0] if row else None

    def _razorpay_plan_id_from_env(self, product_id: str) -> Optional[str]:
        import os

        pid = (product_id or "").strip()
        if not pid:
            return None
        keys = [
            f"RAZORPAY_PLAN_{pid}",
            f"RAZORPAY_PLAN_{pid.upper()}",
        ]
        if pid.startswith("subscription_vip_"):
            keys.append(f"RAZORPAY_SUBSCRIPTION_PLAN_{pid.replace('subscription_vip_', '').upper()}")
        for key in keys:
            val = (os.environ.get(key) or "").strip()
            if val:
                return val
        return None

    def list_razorpay_subscription_plans(self, platform: str = "astroroshni") -> List[dict]:
        """VIP plans available for Razorpay web subscriptions."""
        from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT plan_id, tier_name, discount_percent, google_play_product_id,
                       price, features, razorpay_plan_id
                FROM subscription_plans
                WHERE platform = ?
                  AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}
                  AND google_play_product_id IS NOT NULL
                  AND TRIM(google_play_product_id) <> ''
                  AND COALESCE(discount_percent, 0) > 0
                ORDER BY COALESCE(discount_percent, 0) ASC
                """,
                (platform,),
            )
            rows = cur.fetchall() or []

        from credits.subscription_pricing_util import parse_plan_benefits

        plans = []
        for r in rows:
            product_id = (r[3] or "").strip()
            rz_plan = (r[6] or "").strip() or self._razorpay_plan_id_from_env(product_id)
            if not rz_plan:
                continue
            price = float(r[4]) if r[4] is not None else 0.0
            features_raw = r[5]
            plans.append(
                {
                    "plan_id": r[0],
                    "tier_name": r[1] or "VIP",
                    "discount_percent": int(r[2] or 0),
                    "product_id": product_id,
                    "price_inr": price,
                    "amount_display": f"₹{int(price)}" if price == int(price) else f"₹{price:.2f}",
                    "razorpay_plan_id": rz_plan,
                    "benefits": parse_plan_benefits(features_raw),
                }
            )
        return plans

    def get_plan_by_internal_id(self, plan_id: int) -> Optional[dict]:
        from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT plan_id, tier_name, discount_percent, google_play_product_id, price, razorpay_plan_id
                FROM subscription_plans
                WHERE plan_id = ? AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}
                """,
                (int(plan_id),),
            )
            row = cur.fetchone()
        if not row:
            return None
        product_id = (row[3] or "").strip()
        rz_plan = (row[5] or "").strip() or self._razorpay_plan_id_from_env(product_id)
        return {
            "plan_id": row[0],
            "tier_name": row[1],
            "discount_percent": int(row[2] or 0),
            "product_id": product_id,
            "price_inr": float(row[4]) if row[4] is not None else 0.0,
            "razorpay_plan_id": rz_plan,
        }

    def get_plan_by_razorpay_plan_id(self, razorpay_plan_id: str, platform: str = "astroroshni") -> Optional[dict]:
        """Resolve internal VIP plan from Razorpay plan_id (DB column or env fallback)."""
        rz = (razorpay_plan_id or "").strip()
        if not rz:
            return None
        from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT plan_id, tier_name, discount_percent, google_play_product_id, price, razorpay_plan_id
                FROM subscription_plans
                WHERE platform = ? AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}
                  AND TRIM(COALESCE(razorpay_plan_id, '')) = ?
                """,
                (platform, rz),
            )
            row = cur.fetchone()
        if row:
            product_id = (row[3] or "").strip()
            return {
                "plan_id": row[0],
                "tier_name": row[1],
                "discount_percent": int(row[2] or 0),
                "product_id": product_id,
                "price_inr": float(row[4]) if row[4] is not None else 0.0,
                "razorpay_plan_id": rz,
            }
        for plan in self.list_razorpay_subscription_plans(platform):
            if plan.get("razorpay_plan_id") == rz:
                return self.get_plan_by_internal_id(plan["plan_id"])
        return None

    def user_has_active_google_play_subscription(self, userid: int, platform: str = "astroroshni") -> bool:
        from db import get_conn, execute

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT 1
                FROM user_subscriptions us
                JOIN subscription_plans sp ON sp.plan_id = us.plan_id
                WHERE us.userid = ?
                  AND sp.platform = ?
                  AND us.status = 'active'
                  AND us.end_date >= {self._date_today_expr()}
                  AND COALESCE(us.billing_provider, 'google_play') <> 'razorpay'
                LIMIT 1
                """,
                (userid, platform),
            )
            return bool(cur.fetchone())

    def upsert_razorpay_subscription_map(
        self,
        razorpay_subscription_id: str,
        userid: int,
        internal_plan_id: int,
        product_id: str,
    ) -> None:
        from db import get_conn, execute

        sub_id = (razorpay_subscription_id or "").strip()
        if not sub_id:
            return
        with get_conn() as conn:
            execute(
                conn,
                """
                INSERT INTO razorpay_subscription_map (
                    razorpay_subscription_id, userid, internal_plan_id, product_id, updated_at
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT (razorpay_subscription_id) DO UPDATE
                  SET userid = EXCLUDED.userid,
                      internal_plan_id = EXCLUDED.internal_plan_id,
                      product_id = EXCLUDED.product_id,
                      updated_at = CURRENT_TIMESTAMP
                """,
                (sub_id, userid, internal_plan_id, product_id),
            )
            conn.commit()

    def get_userid_by_razorpay_subscription(self, razorpay_subscription_id: str) -> Optional[int]:
        from db import get_conn, execute

        sub_id = (razorpay_subscription_id or "").strip()
        if not sub_id:
            return None
        with get_conn() as conn:
            cur = execute(
                conn,
                "SELECT userid FROM razorpay_subscription_map WHERE razorpay_subscription_id = ?",
                (sub_id,),
            )
            row = cur.fetchone()
        return int(row[0]) if row else None

    def get_razorpay_subscription_map(self, razorpay_subscription_id: str) -> Optional[dict]:
        from db import get_conn, execute

        sub_id = (razorpay_subscription_id or "").strip()
        if not sub_id:
            return None
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT userid, internal_plan_id, product_id
                FROM razorpay_subscription_map
                WHERE razorpay_subscription_id = ?
                """,
                (sub_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "userid": int(row[0]),
            "internal_plan_id": int(row[1]) if row[1] is not None else None,
            "product_id": row[2],
        }

    def mark_razorpay_subscription_cancel_pending(self, userid: int, razorpay_subscription_id: str) -> bool:
        from db import get_conn, execute

        with get_conn() as conn:
            cur = execute(
                conn,
                """
                UPDATE user_subscriptions
                SET cancel_at_period_end = TRUE
                WHERE userid = ?
                  AND razorpay_subscription_id = ?
                  AND status = 'active'
                """,
                (userid, razorpay_subscription_id.strip()),
            )
            conn.commit()
            return bool(getattr(cur, "rowcount", 0))

    def set_user_subscription(
        self,
        userid: int,
        plan_id: int,
        start_date: str,
        end_date: str,
        google_play_order_id: Optional[str] = None,
        billing_provider: Optional[str] = None,
        razorpay_subscription_id: Optional[str] = None,
        cancel_at_period_end: Optional[bool] = None,
    ) -> bool:
        """
        Set user's subscription entitlement window for a plan.

        Behavior:
        - Keep membership valid until end_date (entitlement window from Play).
        - Idempotent per (userid, plan_id, start_date, end_date): re-sync should not create duplicate rows.
        - Ensure only one current active row on a platform.
        Dates are YYYY-MM-DD.
        Optional google_play_order_id: latest GPA order id from Play (may include ..N renewal suffix).
        """
        from db import get_conn, execute
        from credits.play_order_id_util import normalize_play_order_id

        play_order_id = normalize_play_order_id(google_play_order_id)
        provider = (billing_provider or "").strip().lower() or None
        rz_sub = (razorpay_subscription_id or "").strip() or None
        try:
            with get_conn() as conn:
                cursor = execute(conn, "SELECT platform FROM subscription_plans WHERE plan_id = ?", (plan_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                platform = row[0]

                # Cleanup: rows that are marked active but already lapsed should not stay active.
                today_expr = self._date_today_expr()
                execute(
                    conn,
                    f"""
                    UPDATE user_subscriptions
                    SET status = 'inactive'
                    WHERE userid = ?
                      AND status = 'active'
                      AND end_date < {today_expr}
                      AND plan_id IN (SELECT plan_id FROM subscription_plans WHERE platform = ?)
                    """,
                    (userid, platform),
                )

                # Idempotency key for a single billing cycle entitlement window.
                cursor = execute(
                    conn,
                    """
                    SELECT id
                    FROM user_subscriptions
                    WHERE userid = ?
                      AND plan_id = ?
                      AND DATE(start_date) = DATE(?)
                      AND DATE(end_date) = DATE(?)
                    ORDER BY created_at DESC NULLS LAST, id DESC
                    LIMIT 1
                    """,
                    (userid, plan_id, start_date, end_date),
                )
                existing = cursor.fetchone()

                if existing:
                    keep_id = existing[0]
                    execute(
                        conn,
                        """
                        UPDATE user_subscriptions
                        SET status = 'active',
                            start_date = ?,
                            end_date = ?,
                            google_play_order_id = COALESCE(?, google_play_order_id),
                            billing_provider = COALESCE(?, billing_provider),
                            razorpay_subscription_id = COALESCE(?, razorpay_subscription_id),
                            cancel_at_period_end = COALESCE(?, cancel_at_period_end)
                        WHERE id = ?
                        """,
                        (
                            start_date,
                            end_date,
                            play_order_id,
                            provider,
                            rz_sub,
                            cancel_at_period_end,
                            keep_id,
                        ),
                    )
                    execute(
                        conn,
                        """
                        UPDATE user_subscriptions
                        SET status = 'inactive'
                        WHERE userid = ?
                          AND id <> ?
                          AND status = 'active'
                          AND plan_id IN (SELECT plan_id FROM subscription_plans WHERE platform = ?)
                        """,
                        (userid, keep_id, platform),
                    )
                else:
                    execute(
                        conn,
                        """
                        UPDATE user_subscriptions
                        SET status = 'inactive'
                        WHERE userid = ?
                          AND status = 'active'
                          AND plan_id IN (SELECT plan_id FROM subscription_plans WHERE platform = ?)
                        """,
                        (userid, platform),
                    )
                    execute(
                        conn,
                        """
                        INSERT INTO user_subscriptions (
                            userid, plan_id, start_date, end_date, status,
                            google_play_order_id, billing_provider, razorpay_subscription_id,
                            cancel_at_period_end
                        )
                        VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
                        """,
                        (
                            userid,
                            plan_id,
                            start_date,
                            end_date,
                            play_order_id,
                            provider,
                            rz_sub,
                            bool(cancel_at_period_end) if cancel_at_period_end is not None else False,
                        ),
                    )
                conn.commit()
                return True
        except Exception:
            return False

    def upsert_play_subscription_token(
        self,
        userid: int,
        purchase_token: str,
        product_id: Optional[str] = None,
        latest_order_id: Optional[str] = None,
    ) -> bool:
        """Persist purchase_token -> userid mapping for RTDN processing."""
        from db import get_conn, execute
        from credits.play_order_id_util import normalize_play_order_id

        token = (purchase_token or "").strip()
        if not token:
            return False
        order_id = normalize_play_order_id(latest_order_id)
        try:
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    INSERT INTO play_subscription_token_map (
                        userid, purchase_token, product_id, latest_order_id, created_at, last_seen_at
                    )
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (purchase_token) DO UPDATE
                      SET userid = EXCLUDED.userid,
                          product_id = EXCLUDED.product_id,
                          latest_order_id = COALESCE(EXCLUDED.latest_order_id, play_subscription_token_map.latest_order_id),
                          last_seen_at = CURRENT_TIMESTAMP
                    """,
                    (userid, token, (product_id or "").strip() or None, order_id),
                )
                conn.commit()
                return True
        except Exception:
            return False

    def get_user_id_by_play_purchase_token(self, purchase_token: str) -> Optional[int]:
        """Resolve userid from purchase token map. Returns None when unknown."""
        from db import get_conn, execute
        token = (purchase_token or "").strip()
        if not token:
            return None
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT userid
                    FROM play_subscription_token_map
                    WHERE purchase_token = ?
                    LIMIT 1
                    """,
                    (token,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    return int(row[0])
                except (TypeError, ValueError):
                    return None
        except Exception:
            return None

    def has_processed_play_subscription_event(self, event_id: str) -> bool:
        from db import get_conn, execute
        eid = (event_id or "").strip()
        if not eid:
            return False
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    "SELECT 1 FROM play_subscription_event_log WHERE event_id = ? LIMIT 1",
                    (eid,),
                )
                return bool(cur.fetchone())
        except Exception:
            return False

    def get_latest_subscription_on_platform(self, userid: int, platform: str) -> Optional[dict]:
        """Most recent subscription row for user on platform (any status), for renewal inference."""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT us.plan_id, us.start_date, us.end_date, us.status, sp.plan_name, sp.tier_name
                    FROM user_subscriptions us
                    JOIN subscription_plans sp ON us.plan_id = sp.plan_id
                    WHERE us.userid = ?
                      AND sp.platform = ?
                    ORDER BY us.end_date DESC NULLS LAST, us.created_at DESC NULLS LAST, us.id DESC
                    LIMIT 1
                    """,
                    (userid, platform),
                )
                row = cur.fetchone()
        except Exception:
            row = None
        if not row:
            return None
        return {
            "plan_id": row[0],
            "start_date": str(row[1])[:10] if row[1] else None,
            "end_date": str(row[2])[:10] if row[2] else None,
            "status": row[3],
            "plan_name": row[4],
            "tier_name": row[5],
        }

    def log_play_subscription_event(
        self,
        *,
        event_id: str,
        purchase_token: Optional[str],
        product_id: Optional[str],
        notification_type: Optional[int] = None,
        event_time_millis: Optional[int] = None,
        payload_json: Optional[str] = None,
        userid: Optional[int] = None,
        source: Optional[str] = None,
        event_kind: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        processed_at: Optional[Any] = None,
        google_play_order_id: Optional[str] = None,
    ) -> bool:
        from db import get_conn, execute
        from credits.play_order_id_util import normalize_play_order_id, play_order_id_base

        eid = (event_id or "").strip()
        if not eid:
            return False
        play_order_id = normalize_play_order_id(google_play_order_id)
        order_base = play_order_id_base(play_order_id)
        processed_sql = "CURRENT_TIMESTAMP"
        params: List[Any] = [
            eid,
            (purchase_token or "").strip() or None,
            (product_id or "").strip() or None,
            int(notification_type) if notification_type is not None else None,
            int(event_time_millis) if event_time_millis is not None else None,
            payload_json,
            int(userid) if userid is not None else None,
            (source or "").strip() or None,
            (event_kind or "").strip() or None,
            (start_date or "").strip()[:10] or None,
            (end_date or "").strip()[:10] or None,
            play_order_id,
            order_base,
        ]
        if processed_at is not None:
            processed_sql = "?"
            params.append(processed_at)
        try:
            with get_conn() as conn:
                execute(
                    conn,
                    f"""
                    INSERT INTO play_subscription_event_log (
                        event_id, purchase_token, product_id, notification_type, event_time_millis,
                        payload_json, userid, source, event_kind, start_date, end_date,
                        google_play_order_id, order_id_base, processed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {processed_sql})
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    tuple(params),
                )
                conn.commit()
                return True
        except Exception:
            return False

    def list_admin_subscription_events(
        self,
        from_date: str,
        to_date: str,
        *,
        query: Optional[str] = None,
        event_kind: Optional[str] = None,
        source: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        """Admin list of play_subscription_event_log with user display fields."""
        from db import get_conn, execute
        from credits.play_subscription_events import display_label_for_event

        page = max(1, page)
        limit = max(1, min(200, limit))
        offset = (page - 1) * limit

        base = """
            FROM play_subscription_event_log e
            LEFT JOIN users u ON u.userid = e.userid
            LEFT JOIN play_subscription_token_map m
              ON e.userid IS NULL AND m.purchase_token = e.purchase_token
            LEFT JOIN users u2 ON u2.userid = m.userid
            WHERE DATE(e.processed_at) >= ? AND DATE(e.processed_at) <= ?
        """
        params: list = [from_date, to_date]
        if event_kind and event_kind.strip():
            ek = event_kind.strip().lower()
            if ek == "renewed":
                base += " AND (e.event_kind = 'renewed' OR (e.source = 'rtdn' AND e.notification_type = 2))"
            else:
                base += " AND e.event_kind = ?"
                params.append(ek)
        if source and source.strip():
            base += " AND e.source = ?"
            params.append(source.strip().lower())
        if query and query.strip():
            q = f"%{query.strip()}%"
            base += " AND (u.name ILIKE ? OR u.phone ILIKE ? OR u2.name ILIKE ? OR u2.phone ILIKE ? OR CAST(COALESCE(e.userid, m.userid) AS TEXT) ILIKE ?)"
            params.extend([q, q, q, q, q])

        count_sql = f"SELECT COUNT(*) {base}"
        select_sql = f"""
            SELECT e.id, e.event_id, e.userid, COALESCE(e.userid, m.userid) AS resolved_userid,
                   COALESCE(u.name, u2.name) AS user_name,
                   COALESCE(u.phone, u2.phone) AS user_phone,
                   e.source, e.event_kind, e.notification_type,
                   e.product_id, e.purchase_token, e.start_date, e.end_date,
                   e.google_play_order_id, e.order_id_base,
                   e.event_time_millis, e.processed_at
            {base}
            ORDER BY e.processed_at DESC, e.id DESC
            LIMIT ? OFFSET ?
        """

        with get_conn() as conn:
            cur = execute(conn, count_sql, tuple(params))
            total = int(cur.fetchone()[0] or 0)
            cur = execute(conn, select_sql, tuple(params + [limit, offset]))
            colnames = [d[0] for d in (cur.description or [])]
            rows = cur.fetchall() or []

        events = [self._serialize_admin_subscription_event(dict(zip(colnames, r))) for r in rows]

        return {
            "from_date": from_date,
            "to_date": to_date,
            "page": page,
            "limit": limit,
            "total": total,
            "events": events,
        }

    def _serialize_admin_subscription_event(self, row: dict) -> dict:
        from credits.play_subscription_events import display_label_for_event
        from credits.play_order_id_util import play_order_id_base, play_order_renewal_index

        uid = row.get("resolved_userid") or row.get("userid")
        src = row.get("source") or ""
        kind = row.get("event_kind") or ""
        ntype = row.get("notification_type")
        processed = row.get("processed_at")
        order_id = row.get("google_play_order_id")
        order_base = row.get("order_id_base") or play_order_id_base(order_id)
        return {
            "id": row.get("id"),
            "event_id": row.get("event_id"),
            "userid": uid,
            "user_name": row.get("user_name"),
            "user_phone": row.get("user_phone"),
            "source": src,
            "event_kind": kind,
            "event_label": display_label_for_event(src, kind, ntype),
            "notification_type": ntype,
            "product_id": row.get("product_id"),
            "purchase_token_prefix": (row.get("purchase_token") or "")[:12] or None,
            "google_play_order_id": order_id,
            "order_id_base": order_base,
            "renewal_index": play_order_renewal_index(order_id),
            "start_date": str(row["start_date"])[:10] if row.get("start_date") else None,
            "end_date": str(row["end_date"])[:10] if row.get("end_date") else None,
            "event_time_millis": row.get("event_time_millis"),
            "processed_at": processed.isoformat() if hasattr(processed, "isoformat") else processed,
            "is_renewal": kind == "renewed" or (src == "rtdn" and ntype == 2),
        }

    def list_admin_subscription_event_groups(
        self,
        from_date: str,
        to_date: str,
        *,
        query: Optional[str] = None,
        event_kind: Optional[str] = None,
        source: Optional[str] = None,
        renewals_only: bool = False,
        limit: int = 100,
    ) -> dict:
        """Group subscription events by Play order_id_base (renewal family tree)."""
        from credits.play_order_id_util import play_order_sort_key

        flat = self.list_admin_subscription_events(
            from_date,
            to_date,
            query=query,
            event_kind=event_kind,
            source=source,
            page=1,
            limit=min(5000, max(200, limit * 20)),
        )
        events = flat.get("events") or []
        if renewals_only:
            events = [e for e in events if e.get("is_renewal")]

        groups_map: Dict[str, dict] = {}
        for ev in events:
            base = ev.get("order_id_base") or ev.get("google_play_order_id") or f"unknown-{ev.get('userid')}-{ev.get('product_id')}"
            key = f"{ev.get('userid')}|{ev.get('product_id')}|{base}"
            if key not in groups_map:
                groups_map[key] = {
                    "order_id_base": base,
                    "userid": ev.get("userid"),
                    "user_name": ev.get("user_name"),
                    "user_phone": ev.get("user_phone"),
                    "product_id": ev.get("product_id"),
                    "events": [],
                }
            groups_map[key]["events"].append(ev)

        groups = []
        for g in groups_map.values():
            g["events"].sort(
                key=lambda e: (
                    play_order_sort_key(e.get("google_play_order_id")),
                    e.get("processed_at") or "",
                )
            )
            groups.append(g)
        groups.sort(
            key=lambda g: (
                (g.get("events") or [{}])[-1].get("processed_at") or "",
                g.get("order_id_base") or "",
            ),
            reverse=True,
        )
        return {
            "from_date": from_date,
            "to_date": to_date,
            "total_groups": len(groups),
            "groups": groups[:limit],
        }

    @staticmethod
    def _infer_backfill_event_kind(prior: Optional[dict], plan_id: int, start_date: str, end_date: str) -> str:
        if not prior:
            return "purchased"
        try:
            prior_plan = int(prior.get("plan_id"))
        except (TypeError, ValueError):
            prior_plan = None
        if prior_plan is not None and prior_plan != plan_id:
            return "upgraded"
        prior_end = (prior.get("end_date") or "")[:10]
        prior_start = (prior.get("start_date") or "")[:10]
        if prior_end and end_date and end_date > prior_end:
            return "renewed"
        if prior_start == start_date and prior_end == end_date:
            return "synced"
        return "updated"

    def backfill_subscription_events_from_history(self, *, dry_run: bool = True) -> dict:
        """
        One-time style backfill: create play_subscription_event_log rows from existing
        user_subscriptions (paid plans). Idempotent via event_id backfill|sub|{id}.
        Does not call Google Play API.
        """
        from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE

        select_sql = f"""
            SELECT us.id, us.userid, us.plan_id, us.start_date, us.end_date, us.status,
                   us.created_at, us.google_play_order_id,
                   sp.platform, sp.google_play_product_id, sp.plan_name
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.plan_id
            WHERE (
                (sp.google_play_product_id IS NOT NULL AND TRIM(sp.google_play_product_id) <> '')
                OR COALESCE(sp.price, 0) > 0
            )
            ORDER BY us.userid ASC, sp.platform ASC,
                     COALESCE(us.created_at, us.start_date::timestamp) ASC NULLS LAST,
                     us.id ASC
        """
        with get_conn() as conn:
            cur = execute(conn, select_sql)
            colnames = [d[0] for d in (cur.description or [])]
            sub_rows = [dict(zip(colnames, r)) for r in (cur.fetchall() or [])]

            cur = execute(
                conn,
                """
                SELECT userid, purchase_token, product_id
                FROM play_subscription_token_map
                ORDER BY last_seen_at DESC NULLS LAST, created_at DESC NULLS LAST
                """,
            )
            token_by_user: Dict[int, Dict[str, Optional[str]]] = {}
            for r in cur.fetchall() or []:
                uid = int(r[0])
                if uid not in token_by_user:
                    token_by_user[uid] = {
                        "purchase_token": r[1],
                        "product_id": r[2],
                    }

        prior_by_platform: Dict[tuple, dict] = {}
        stats = {
            "dry_run": dry_run,
            "subscription_rows_scanned": len(sub_rows),
            "events_would_insert": 0,
            "events_inserted": 0,
            "events_skipped_existing": 0,
            "by_kind": {},
        }
        preview: List[dict] = []

        for row in sub_rows:
            sub_id = row.get("id")
            userid = int(row.get("userid"))
            plan_id = int(row.get("plan_id"))
            platform = (row.get("platform") or "").strip() or "unknown"
            start_date = str(row.get("start_date") or "")[:10]
            end_date = str(row.get("end_date") or "")[:10]
            if not start_date or not end_date:
                continue

            key = (userid, platform)
            prior = prior_by_platform.get(key)
            kind = self._infer_backfill_event_kind(prior, plan_id, start_date, end_date)
            prior_by_platform[key] = {
                "plan_id": plan_id,
                "start_date": start_date,
                "end_date": end_date,
            }

            stats["by_kind"][kind] = stats["by_kind"].get(kind, 0) + 1
            event_id = f"backfill|sub|{sub_id}"
            token_info = token_by_user.get(userid) or {}
            product_id = (row.get("google_play_product_id") or token_info.get("product_id") or "").strip() or None
            purchase_token = token_info.get("purchase_token")

            created = row.get("created_at")
            processed_note = created.isoformat() if hasattr(created, "isoformat") else str(created or start_date)

            entry = {
                "event_id": event_id,
                "userid": userid,
                "platform": platform,
                "plan_name": row.get("plan_name"),
                "event_kind": kind,
                "start_date": start_date,
                "end_date": end_date,
                "processed_at": processed_note,
            }
            if len(preview) < 25:
                preview.append(entry)

            if dry_run:
                stats["events_would_insert"] += 1
                continue

            if self.has_processed_play_subscription_event(event_id):
                stats["events_skipped_existing"] += 1
                continue

            ok = self.log_play_subscription_event(
                event_id=event_id,
                purchase_token=purchase_token,
                product_id=product_id,
                userid=userid,
                source="backfill",
                event_kind=kind,
                start_date=start_date,
                end_date=end_date,
                processed_at=created if created is not None else None,
                payload_json='{"note":"backfilled from user_subscriptions history"}',
                google_play_order_id=row.get("google_play_order_id"),
            )
            if ok:
                stats["events_inserted"] += 1
            else:
                stats["events_skipped_existing"] += 1

        stats["preview"] = preview
        return stats

    def backfill_subscription_order_ids_from_play(
        self,
        *,
        dry_run: bool = True,
        limit: Optional[int] = None,
        sleep_seconds: float = 0.15,
    ) -> dict:
        """
        Call Google Play for each known subscription purchase_token and store the
        latest GPA order id on token map, matching user_subscriptions period, and events.

        Limitation: Play returns the latest order for that token, not full ..0, ..1 history.
        Rows without a token in play_subscription_token_map are skipped.
        """
        import time
        from db import get_conn, execute
        from credits.play_order_id_util import normalize_play_order_id, play_order_id_base

        try:
            from credits.routes import (
                PACKAGE_NAME,
                _fetch_google_play_subscription_purchase,
                _subscription_order_id_from_purchase,
                _subscription_period_dates_from_purchase,
            )
        except Exception as e:
            return {"error": f"Could not load Play API helpers: {e}", "dry_run": dry_run}

        select_sql = """
            SELECT userid, purchase_token, product_id, latest_order_id
            FROM play_subscription_token_map
            WHERE purchase_token IS NOT NULL AND TRIM(purchase_token) <> ''
            ORDER BY last_seen_at DESC NULLS LAST, created_at DESC NULLS LAST
        """
        if limit is not None and limit > 0:
            select_sql += f" LIMIT {int(limit)}"

        with get_conn() as conn:
            cur = execute(conn, select_sql)
            tokens = [
                {
                    "userid": int(r[0]),
                    "purchase_token": (r[1] or "").strip(),
                    "product_id": (r[2] or "").strip(),
                    "existing_order_id": (r[3] or "").strip() or None,
                }
                for r in (cur.fetchall() or [])
            ]

        stats: Dict[str, Any] = {
            "dry_run": dry_run,
            "tokens_scanned": len(tokens),
            "play_ok": 0,
            "play_errors": 0,
            "order_ids_found": 0,
            "token_map_updated": 0,
            "subscriptions_updated": 0,
            "events_updated": 0,
            "skipped_no_product": 0,
            "errors": [],
            "preview": [],
        }

        for row in tokens:
            userid = row["userid"]
            token = row["purchase_token"]
            product_id = row["product_id"]
            if not product_id:
                stats["skipped_no_product"] += 1
                continue

            plan_id = self.get_plan_id_by_google_play_product_id(product_id)
            if not plan_id:
                stats["skipped_no_product"] += 1
                continue

            try:
                purchase = _fetch_google_play_subscription_purchase(
                    PACKAGE_NAME, product_id, token
                )
                stats["play_ok"] += 1
            except Exception as e:
                stats["play_errors"] += 1
                if len(stats["errors"]) < 20:
                    stats["errors"].append(
                        {"userid": userid, "product_id": product_id, "error": str(e)[:200]}
                    )
                continue

            order_id = _subscription_order_id_from_purchase(purchase)
            if not order_id:
                continue
            stats["order_ids_found"] += 1
            order_base = play_order_id_base(order_id)
            start_date, end_date = _subscription_period_dates_from_purchase(purchase)

            entry = {
                "userid": userid,
                "product_id": product_id,
                "order_id": order_id,
                "order_id_base": order_base,
                "start_date": start_date,
                "end_date": end_date,
            }
            if len(stats["preview"]) < 25:
                stats["preview"].append(entry)

            if dry_run:
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                continue

            try:
                with get_conn() as conn:
                    execute(
                        conn,
                        """
                        UPDATE play_subscription_token_map
                        SET latest_order_id = ?
                        WHERE purchase_token = ?
                        """,
                        (order_id, token),
                    )
                    stats["token_map_updated"] += 1

                    cur = execute(
                        conn,
                        """
                        UPDATE user_subscriptions
                        SET google_play_order_id = ?
                        WHERE userid = ?
                          AND plan_id = ?
                          AND DATE(start_date) = DATE(?)
                          AND DATE(end_date) = DATE(?)
                          AND (google_play_order_id IS NULL OR TRIM(google_play_order_id) = '')
                        """,
                        (order_id, userid, plan_id, start_date, end_date),
                    )
                    if getattr(cur, "rowcount", 0):
                        stats["subscriptions_updated"] += int(cur.rowcount)

                    if getattr(cur, "rowcount", 0) == 0:
                        cur2 = execute(
                            conn,
                            """
                            UPDATE user_subscriptions
                            SET google_play_order_id = ?
                            WHERE id = (
                                SELECT id FROM user_subscriptions
                                WHERE userid = ?
                                  AND plan_id = ?
                                  AND (google_play_order_id IS NULL OR TRIM(google_play_order_id) = '')
                                ORDER BY end_date DESC NULLS LAST, id DESC
                                LIMIT 1
                            )
                            """,
                            (order_id, userid, plan_id),
                        )
                        if getattr(cur2, "rowcount", 0):
                            stats["subscriptions_updated"] += int(cur2.rowcount)

                    cur3 = execute(
                        conn,
                        """
                        UPDATE play_subscription_event_log
                        SET google_play_order_id = ?,
                            order_id_base = ?
                        WHERE purchase_token = ?
                          AND (google_play_order_id IS NULL OR TRIM(google_play_order_id) = '')
                        """,
                        (order_id, order_base, token),
                    )
                    if getattr(cur3, "rowcount", 0):
                        stats["events_updated"] += int(cur3.rowcount)

                    conn.commit()
            except Exception as e:
                stats["play_errors"] += 1
                if len(stats["errors"]) < 20:
                    stats["errors"].append(
                        {"userid": userid, "product_id": product_id, "error": str(e)[:200]}
                    )

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        return stats

    def has_processed_play_onetime_event(self, event_id: str) -> bool:
        from db import get_conn, execute
        eid = (event_id or "").strip()
        if not eid:
            return False
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    "SELECT 1 FROM play_onetime_event_log WHERE event_id = ? LIMIT 1",
                    (eid,),
                )
                return bool(cur.fetchone())
        except Exception:
            return False

    def enqueue_pending_play_onetime_event(
        self,
        *,
        event_id: str,
        purchase_token: str,
        product_id: Optional[str],
        notification_type: Optional[int],
        event_time_millis: Optional[int],
        payload_json: Optional[str],
        userid: Optional[int] = None,
        resolution_note: Optional[str] = None,
    ) -> bool:
        from db import get_conn, execute
        eid = (event_id or "").strip()
        token = (purchase_token or "").strip()
        if not eid or not token:
            return False
        try:
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    INSERT INTO play_onetime_pending_event (
                        event_id,
                        purchase_token,
                        product_id,
                        notification_type,
                        event_time_millis,
                        payload_json,
                        userid,
                        status,
                        first_seen_at,
                        last_retry_at,
                        retry_count,
                        resolution_note,
                        last_error
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, ?, NULL)
                    ON CONFLICT (event_id) DO UPDATE
                      SET purchase_token = EXCLUDED.purchase_token,
                          product_id = EXCLUDED.product_id,
                          notification_type = EXCLUDED.notification_type,
                          event_time_millis = EXCLUDED.event_time_millis,
                          payload_json = COALESCE(EXCLUDED.payload_json, play_onetime_pending_event.payload_json),
                          userid = COALESCE(EXCLUDED.userid, play_onetime_pending_event.userid),
                          status = CASE
                              WHEN play_onetime_pending_event.status = 'resolved' THEN play_onetime_pending_event.status
                              ELSE 'pending'
                          END,
                          resolution_note = COALESCE(EXCLUDED.resolution_note, play_onetime_pending_event.resolution_note),
                          last_retry_at = CURRENT_TIMESTAMP
                    """,
                    (
                        eid,
                        token,
                        (product_id or "").strip() or None,
                        int(notification_type) if notification_type is not None else None,
                        int(event_time_millis) if event_time_millis is not None else None,
                        payload_json,
                        int(userid) if userid is not None else None,
                        (resolution_note or "").strip() or None,
                    ),
                )
                conn.commit()
                return True
        except Exception:
            return False

    def get_pending_play_onetime_events(
        self,
        *,
        purchase_token: Optional[str] = None,
        userid: Optional[int] = None,
        limit: int = 100,
    ):
        from db import get_conn, execute
        clauses = ["status = 'pending'"]
        params = []
        token = (purchase_token or "").strip()
        if token:
            clauses.append("purchase_token = ?")
            params.append(token)
        if userid is not None:
            clauses.append("(userid = ? OR userid IS NULL)")
            params.append(int(userid))
        lim = max(1, min(int(limit or 100), 500))
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    f"""
                    SELECT event_id,
                           purchase_token,
                           product_id,
                           notification_type,
                           event_time_millis,
                           payload_json,
                           userid,
                           retry_count,
                           first_seen_at,
                           last_retry_at,
                           resolution_note,
                           last_error
                    FROM play_onetime_pending_event
                    WHERE {' AND '.join(clauses)}
                    ORDER BY COALESCE(event_time_millis, 0) ASC, first_seen_at ASC
                    LIMIT {lim}
                    """,
                    tuple(params),
                )
                return cur.fetchall() or []
        except Exception:
            return []

    def mark_pending_play_onetime_event_retry(
        self,
        event_id: str,
        *,
        userid: Optional[int] = None,
        last_error: Optional[str] = None,
    ) -> bool:
        from db import get_conn, execute
        eid = (event_id or "").strip()
        if not eid:
            return False
        try:
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    UPDATE play_onetime_pending_event
                    SET retry_count = COALESCE(retry_count, 0) + 1,
                        last_retry_at = CURRENT_TIMESTAMP,
                        userid = COALESCE(?, userid),
                        last_error = ?,
                        status = 'pending'
                    WHERE event_id = ?
                    """,
                    (
                        int(userid) if userid is not None else None,
                        (last_error or "").strip()[:500] or None,
                        eid,
                    ),
                )
                conn.commit()
                return True
        except Exception:
            return False

    def resolve_pending_play_onetime_event(
        self,
        event_id: str,
        *,
        userid: Optional[int] = None,
        status: str = "resolved",
        resolution_note: Optional[str] = None,
        last_error: Optional[str] = None,
    ) -> bool:
        from db import get_conn, execute
        eid = (event_id or "").strip()
        if not eid:
            return False
        normalized_status = (status or "resolved").strip() or "resolved"
        try:
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    UPDATE play_onetime_pending_event
                    SET userid = COALESCE(?, userid),
                        status = ?,
                        resolved_at = CURRENT_TIMESTAMP,
                        last_retry_at = CURRENT_TIMESTAMP,
                        resolution_note = ?,
                        last_error = ?
                    WHERE event_id = ?
                    """,
                    (
                        int(userid) if userid is not None else None,
                        normalized_status,
                        (resolution_note or "").strip()[:500] or None,
                        (last_error or "").strip()[:500] or None,
                        eid,
                    ),
                )
                conn.commit()
                return True
        except Exception:
            return False

    def upsert_play_onetime_token(self, userid: int, purchase_token: str, product_id: Optional[str] = None) -> bool:
        """Persist one-time purchase token -> userid mapping for RTDN processing."""
        from db import get_conn, execute
        token = (purchase_token or "").strip()
        if not token:
            return False
        try:
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    INSERT INTO play_onetime_token_map (userid, purchase_token, product_id, created_at, last_seen_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (purchase_token) DO UPDATE
                      SET userid = EXCLUDED.userid,
                          product_id = EXCLUDED.product_id,
                          last_seen_at = CURRENT_TIMESTAMP
                    """,
                    (userid, token, (product_id or "").strip() or None),
                )
                conn.commit()
                return True
        except Exception:
            return False

    def get_user_id_by_play_onetime_purchase_token(self, purchase_token: str) -> Optional[int]:
        """Resolve userid from one-time purchase token map. Returns None when unknown."""
        from db import get_conn, execute
        token = (purchase_token or "").strip()
        if not token:
            return None
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT userid
                    FROM play_onetime_token_map
                    WHERE purchase_token = ?
                    LIMIT 1
                    """,
                    (token,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    return int(row[0])
                except (TypeError, ValueError):
                    return None
        except Exception:
            return None

    def log_play_onetime_event(
        self,
        *,
        event_id: str,
        purchase_token: Optional[str],
        product_id: Optional[str],
        notification_type: Optional[int],
        event_time_millis: Optional[int],
        payload_json: Optional[str],
    ) -> bool:
        from db import get_conn, execute
        eid = (event_id or "").strip()
        if not eid:
            return False
        try:
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    INSERT INTO play_onetime_event_log (
                        event_id, purchase_token, product_id, notification_type, event_time_millis, payload_json, processed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (
                        eid,
                        (purchase_token or "").strip() or None,
                        (product_id or "").strip() or None,
                        int(notification_type) if notification_type is not None else None,
                        int(event_time_millis) if event_time_millis is not None else None,
                        payload_json,
                    ),
                )
                conn.commit()
                return True
        except Exception:
            return False

    def expire_user_subscription_for_platform(self, userid: int, platform: str = "astroroshni") -> bool:
        """Expire only already-lapsed subscriptions.

        Older mobile builds call this when Play does not return a purchase token. That can happen for
        cancelled-but-paid-through subscriptions, so future end_date rows must be preserved.
        """
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                end_expr = self._date_yesterday_expr()
                today_expr = self._date_today_expr()
                cursor = execute(
                    conn,
                    f"""
                    UPDATE user_subscriptions
                    SET end_date = {end_expr}
                    WHERE userid = ? AND status = 'active'
                      AND end_date < {today_expr}
                      AND plan_id IN (SELECT plan_id FROM subscription_plans WHERE platform = ?)
                    """,
                    (userid, platform),
                )
                conn.commit()
                return (cursor.rowcount or 0) > 0
        except Exception:
            return False

    def get_effective_cost(self, userid: int, base_cost: int, setting_key: str = None) -> int:
        """Return cost for user. Non-VIP: returns base_cost (site effective/discounted price).
        VIP: applies subscription % off the original price (from setting_key), not the discounted price."""
        if base_cost <= 0:
            return base_cost
        discount = self.get_subscription_discount_percent(userid)
        if discount <= 0:
            return base_cost  # Non-VIP: effective (discounted) price
        # VIP: apply discount on original price, not on already-discounted base_cost
        if setting_key:
            _, original, _ = self.get_credit_setting_and_original(setting_key)
            base_cost = original
        return max(1, round(base_cost * (100 - discount) / 100))

    def get_free_chat_question_used(self, userid: int) -> bool:
        """True if user has already used their one free standard chat question."""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                cursor = execute(conn, "SELECT free_chat_question_used FROM user_credits WHERE userid = ?", (userid,))
                row = cursor.fetchone()
        except Exception:
            row = None
        return bool(row and row[0])

    @staticmethod
    def create_free_question_birth_hash(birth_details: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Canonical hash for free-question policy (aligned with birth_charts.birth_hash).
        """
        from utils.birth_hash import birth_hash_from_birth_details_dict

        return birth_hash_from_birth_details_dict(birth_details)

    def get_free_chat_birth_hash_used(self, birth_hash: Optional[str]) -> bool:
        """True if any account has already consumed free question for this birth hash."""
        if not birth_hash:
            return False
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    "SELECT 1 FROM free_chat_birth_hash_usage WHERE birth_hash = ? LIMIT 1",
                    (birth_hash,),
                )
                return cur.fetchone() is not None
        except Exception:
            return False

    def prior_paid_chat_usage_exists_for_birth_hash(self, birth_hash: Optional[str]) -> bool:
        """
        True if this birth hash already had a *real* assistant reply (not clarification-only).

        chat-v2 persists the user row in ``chat_messages`` before intent routing, so a turn that
        ends in ``message_type = 'clarification'`` still has ``sender = 'user'``. Counting bare
        user rows would incorrectly block the free question on the user's *next* message (reply to
        clarification). We only treat history as "prior usage" when there is a completed assistant
        message after some user message with a non-clarification ``message_type`` (NULL/legacy
        rows count as a normal answer).
        """
        if not birth_hash:
            return False
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT 1
                    FROM chat_messages mu
                    INNER JOIN chat_sessions s ON s.session_id = mu.session_id
                    INNER JOIN birth_charts bc ON bc.id = s.birth_chart_id
                    INNER JOIN chat_messages ma ON ma.session_id = s.session_id
                      AND ma.sender = 'assistant'
                      AND ma.message_id > mu.message_id
                      AND ma.status = 'completed'
                      AND COALESCE(NULLIF(TRIM(ma.message_type), ''), 'answer') NOT IN ('clarification', 'native_gate')
                    WHERE bc.birth_hash = ?
                      AND mu.sender = 'user'
                    LIMIT 1
                    """,
                    (birth_hash,),
                )
                return cur.fetchone() is not None
        except Exception:
            return False

    def user_has_registered_push_token(self, userid: int) -> bool:
        """True if the user has at least one Expo push token (app enabled notifications enough to register)."""
        from db import get_conn, execute
        try:
            from nudge_engine import db as nudge_db

            with get_conn() as conn:
                nudge_db.init_nudge_tables(conn)
                cur = execute(conn, "SELECT 1 FROM device_tokens WHERE userid = ? LIMIT 1", (userid,))
                return cur.fetchone() is not None
        except Exception:
            return False

    def get_web_notifications_granted(self, userid: int) -> bool:
        """Web client: set via POST /credits/web-notification-opt-in when Notification.permission is granted."""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    "SELECT COALESCE(web_notifications_granted, 0) FROM user_credits WHERE userid = ?",
                    (userid,),
                )
                row = cur.fetchone()
                return bool(row and row[0])
        except Exception:
            return False

    def set_web_notifications_granted(self, userid: int, granted: bool = True) -> None:
        from db import get_conn, execute

        val = 1 if granted else 0
        with get_conn() as conn:
            cur = execute(
                conn,
                "UPDATE user_credits SET web_notifications_granted = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
                (val, userid),
            )
            if getattr(cur, "rowcount", 0) == 0:
                bal = self.get_user_credits(userid)
                self._upsert_user_credits(conn, userid, bal)
                execute(
                    conn,
                    "UPDATE user_credits SET web_notifications_granted = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
                    (val, userid),
                )
            conn.commit()

    def notification_opt_in_satisfied_for_free_question(self, userid: int) -> bool:
        """Free first question no longer requires push or web notification opt-in (userid kept for API stability)."""
        return True

    def is_free_standard_chat_question_available(self, userid: int) -> bool:
        """Unused one-time free standard chat AND notifications requirement met."""
        if self.get_free_chat_question_used(userid):
            return False
        return self.notification_opt_in_satisfied_for_free_question(userid)

    def is_free_standard_chat_question_available_for_birth_hash(
        self, userid: int, birth_hash: Optional[str]
    ) -> bool:
        """
        Free question is available only when:
        - user has not consumed their one-time free question,
        - notifications requirement is met,
        - and this birth hash has not consumed free question globally.
        """
        if not self.is_free_standard_chat_question_available(userid):
            return False
        if not birth_hash:
            return False
        if self.get_free_chat_birth_hash_used(birth_hash):
            return False
        if self.prior_paid_chat_usage_exists_for_birth_hash(birth_hash):
            return False
        return True

    def free_question_pending_notification_opt_in(self, userid: int) -> bool:
        """True when the user still has their free question unused but has not met the notification requirement."""
        if self.get_free_chat_question_used(userid):
            return False
        return not self.notification_opt_in_satisfied_for_free_question(userid)

    def mark_free_chat_question_used(self, userid: int, birth_hash: Optional[str] = None) -> None:
        """Mark free question used for user and optionally for global birth-hash gate. Idempotent."""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                cursor = execute(
                    conn,
                    "UPDATE user_credits SET free_chat_question_used = 1, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
                    (userid,),
                )
                if (cursor.rowcount or 0) == 0:
                    # No row yet: insert one with 0 credits and flag set (user still has 0 balance)
                    self._upsert_user_credits(conn, userid, 0, free_used=1)
                if birth_hash:
                    execute(
                        conn,
                        """
                        INSERT INTO free_chat_birth_hash_usage (birth_hash, first_userid, created_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT (birth_hash) DO NOTHING
                        """,
                        (birth_hash, userid),
                    )
                conn.commit()
        except Exception:
            return

    def record_zero_cost_feature_usage(self, userid: int, feature: str, description: str = None) -> bool:
        """Record a feature usage transaction with 0 credit impact (for free/waived usages)."""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                current_balance = self.get_user_credits(userid)
                execute(
                    conn,
                    """
                    INSERT INTO credit_transactions
                    (userid, transaction_type, amount, balance_after, source, reference_id, description)
                    VALUES (?, 'spent', 0, ?, 'feature_usage', ?, ?)
                    """,
                    (userid, current_balance, feature, description),
                )
                conn.commit()
            return True
        except Exception:
            logger.exception(
                "record_zero_cost_feature_usage failed userid=%s feature=%s",
                userid,
                feature,
            )
            return False
    
    def has_transaction_with_reference(self, userid: int, source: str, reference_id: str) -> bool:
        """Return True if a transaction already exists with this source and reference_id (for idempotency)."""
        if not reference_id:
            return False
        from db import get_conn, execute
        with get_conn() as conn:
            cursor = execute(
                conn,
                "SELECT 1 FROM credit_transactions WHERE userid = ? AND source = ? AND reference_id = ? LIMIT 1",
                (userid, source, reference_id),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def calculate_first_purchase_bonus_credits(
        purchased_credits: int,
        config: Optional[Dict[str, Any]] = None,
        *,
        product_id: Optional[str] = None,
    ) -> int:
        """Calculate extra credits from admin settings with optional product-specific overrides."""
        if config is None:
            from utils.admin_settings import get_first_purchase_bonus_config

            config = get_first_purchase_bonus_config()
        try:
            base = max(0, int(purchased_credits))
        except (TypeError, ValueError):
            return 0
        product_key = str(product_id or "").strip()
        effective_config = dict(config or {})
        pack_overrides = config.get("pack_overrides") if isinstance(config, dict) else None
        if product_key and isinstance(pack_overrides, dict):
            override = pack_overrides.get(product_key)
            if isinstance(override, dict):
                effective_config.update(
                    {
                        "percent": override.get("percent", effective_config.get("percent")),
                        "fixed_credits": override.get("fixed_credits", effective_config.get("fixed_credits")),
                        "max_bonus_credits": override.get("max_bonus_credits", effective_config.get("max_bonus_credits")),
                        "bonus_type": override.get("bonus_type", effective_config.get("bonus_type")),
                    }
                )
        percent = max(0, int(effective_config.get("percent") or 0))
        fixed = max(0, int(effective_config.get("fixed_credits") or 0))
        max_bonus = max(0, int(effective_config.get("max_bonus_credits") or 0))
        bonus_type = str(effective_config.get("bonus_type") or "").strip().lower()
        if bonus_type == "fixed" or (fixed > 0 and bonus_type not in {"percent", "none"}):
            bonus = fixed
        elif bonus_type == "percent" or percent > 0:
            bonus = int(base * percent / 100)
        else:
            bonus = 0
        if max_bonus > 0:
            bonus = min(bonus, max_bonus)
        return max(0, bonus)

    def _recent_free_chat_question_row(self, userid: int, window_minutes: int) -> Optional[Dict[str, Any]]:
        from db import get_conn, execute

        try:
            minutes = max(1, int(window_minutes))
        except (TypeError, ValueError):
            minutes = 30
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT id, created_at
                    FROM credit_transactions
                    WHERE userid = ?
                      AND source = 'feature_usage'
                      AND reference_id = 'chat_question'
                      AND amount = 0
                      AND created_at >= CURRENT_TIMESTAMP - (? * INTERVAL '1 minute')
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (userid, minutes),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {"id": row[0], "created_at": row[1]}
        except Exception:
            logger.exception(
                "recent_free_chat_question_lookup failed userid=%s window_minutes=%s",
                userid,
                minutes,
            )
            return None

    def _has_prior_credit_purchase(
        self,
        userid: int,
        *,
        current_source: Optional[str] = None,
        current_reference_id: Optional[str] = None,
    ) -> bool:
        from db import get_conn, execute

        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT 1
                    FROM credit_transactions
                    WHERE userid = ?
                      AND transaction_type = 'earned'
                      AND amount > 0
                      AND source IN ('google_play', 'razorpay')
                      AND NOT (source = ? AND reference_id = ?)
                    LIMIT 1
                    """,
                    (userid, current_source or "", current_reference_id or ""),
                )
                return cur.fetchone() is not None
        except Exception:
            return True

    def _build_resolved_bonus_config(self, config: Dict[str, Any], product_id: Optional[str]) -> Optional[Dict[str, Any]]:
        normalized_product_id = str(product_id or "").strip() or None
        if not normalized_product_id:
            return None
        if isinstance(config.get("pack_overrides"), dict):
            override = config["pack_overrides"].get(normalized_product_id)
            if isinstance(override, dict):
                return {
                    "percent": int(override.get("percent") or 0),
                    "fixed_credits": int(override.get("fixed_credits") or 0),
                    "max_bonus_credits": int(override.get("max_bonus_credits") or 0),
                    "bonus_type": str(override.get("bonus_type") or "none"),
                    "source": "pack_override",
                }
        return {
            "percent": int(config.get("percent") or 0),
            "fixed_credits": int(config.get("fixed_credits") or 0),
            "max_bonus_credits": int(config.get("max_bonus_credits") or 0),
            "bonus_type": str(config.get("bonus_type") or "none"),
            "source": "default",
        }

    def _compose_bonus_status(
        self,
        base_status: Dict[str, Any],
        *,
        purchased_credits: Optional[int] = None,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        config = dict(base_status)
        normalized_product_id = str(product_id or "").strip() or None
        bonus = self.calculate_first_purchase_bonus_credits(
            purchased_credits or 0,
            config,
            product_id=normalized_product_id,
        ) if purchased_credits else 0
        status = {
            **base_status,
            "bonus_credits": bonus,
            "total_credits": (int(purchased_credits or 0) + bonus) if purchased_credits else None,
            "product_id": normalized_product_id,
        }
        resolved_bonus_config = self._build_resolved_bonus_config(config, normalized_product_id)
        if resolved_bonus_config is not None:
            status["resolved_bonus_config"] = resolved_bonus_config
        if status.get("eligible") and bonus <= 0:
            status["eligible"] = False
            status["reason"] = "zero_bonus"
        return status

    def _first_purchase_bonus_base_status(
        self,
        userid: int,
        *,
        current_source: Optional[str] = None,
        current_reference_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from utils.admin_settings import (
            first_purchase_bonus_enabled_for_user,
            get_first_purchase_bonus_config,
            is_first_purchase_bonus_enabled,
        )

        config = get_first_purchase_bonus_config()
        feature_enabled = is_first_purchase_bonus_enabled()
        user_allowed = first_purchase_bonus_enabled_for_user(userid)
        free_used = self.get_free_chat_question_used(userid)
        prior_purchase = self._has_prior_credit_purchase(
            userid,
            current_source=current_source,
            current_reference_id=current_reference_id,
        )
        status: Dict[str, Any] = {
            "enabled": feature_enabled,
            "eligible": False,
            **config,
        }
        if not user_allowed:
            status["reason"] = "feature_disabled_or_user_not_allowed"
            return status
        if not free_used:
            status["reason"] = "free_question_not_used"
            return status
        if prior_purchase:
            status["reason"] = "prior_purchase_exists"
            return status
        free_row = self._recent_free_chat_question_row(userid, config["window_minutes"])
        if not free_row:
            status["reason"] = "outside_bonus_window"
            return status
        if self.has_first_purchase_bonus(userid):
            status["reason"] = "bonus_already_granted"
            status["free_question_transaction_id"] = free_row.get("id")
            return status
        status["eligible"] = True
        status["reason"] = "eligible"
        status["free_question_transaction_id"] = free_row.get("id")
        created_at = free_row.get("created_at")
        if created_at:
            try:
                status["expires_at"] = (created_at + timedelta(minutes=int(config["window_minutes"]))).isoformat()
            except Exception:
                pass
        return status

    def _purchase_discount_base_status(
        self,
        userid: int,
        *,
        current_source: Optional[str] = None,
        current_reference_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from datetime import datetime, timedelta, timezone
        from utils.admin_settings import (
            get_purchase_discount_config,
            get_purchase_discount_window_started_at,
            is_purchase_discount_enabled,
            purchase_discount_enabled_for_user,
        )

        config = get_purchase_discount_config()
        feature_enabled = is_purchase_discount_enabled()
        user_allowed = purchase_discount_enabled_for_user(userid)
        status: Dict[str, Any] = {
            "enabled": feature_enabled,
            "eligible": False,
            **config,
        }
        if not user_allowed:
            status["reason"] = "feature_disabled_or_user_not_allowed"
            return status

        window_minutes = int(config.get("window_minutes") or 0)
        if window_minutes > 0:
            started_at = get_purchase_discount_window_started_at()
            if not started_at:
                status["reason"] = "campaign_window_not_started"
                return status
            expires_at = started_at + timedelta(minutes=window_minutes)
            status["expires_at"] = expires_at.isoformat()
            now = datetime.now(timezone.utc)
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at:
                status["reason"] = "outside_campaign_window"
                return status

        if current_source and current_reference_id:
            reference_id = f"{current_source}:{current_reference_id}"
            if self.has_transaction_with_reference(userid, "purchase_discount", reference_id):
                status["reason"] = "discount_already_granted_for_purchase"
                return status

        status["eligible"] = True
        status["reason"] = "eligible"
        return status

    def get_first_purchase_bonus_status(
        self,
        userid: int,
        purchased_credits: Optional[int] = None,
        *,
        product_id: Optional[str] = None,
        current_source: Optional[str] = None,
        current_reference_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return current eligibility and preview values for the post-free-question purchase bonus."""
        status = self._first_purchase_bonus_base_status(
            userid,
            current_source=current_source,
            current_reference_id=current_reference_id,
        )
        status = self._compose_bonus_status(
            status,
            purchased_credits=purchased_credits,
            product_id=product_id,
        )

        def _log_status(reason: str, extra: Optional[Dict[str, Any]] = None) -> None:
            try:
                logger.debug(
                    "first_purchase_bonus_status userid=%s eligible=%s reason=%s "
                    "enabled=%s user_allowed=%s free_used=%s prior_purchase=%s "
                    "purchased_credits=%s product_id=%s bonus_credits=%s window_minutes=%s extra=%s",
                    userid,
                    bool(status.get("eligible")),
                    reason,
                    status.get("enabled"),
                    None,
                    None,
                    None,
                    purchased_credits,
                    status.get("product_id"),
                    status.get("bonus_credits"),
                    status.get("window_minutes"),
                    extra or {},
                )
            except Exception:
                pass

        _log_status(
            status["reason"],
            {
                "free_question_transaction_id": status.get("free_question_transaction_id"),
                "expires_at": status.get("expires_at"),
            },
        )
        return status

    def has_first_purchase_bonus(self, userid: int) -> bool:
        from db import get_conn, execute

        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    "SELECT 1 FROM credit_transactions WHERE userid = ? AND source = 'first_purchase_bonus' LIMIT 1",
                    (userid,),
                )
                return cur.fetchone() is not None
        except Exception:
            return True

    def maybe_apply_first_purchase_bonus(
        self,
        *,
        userid: int,
        purchased_credits: int,
        purchase_source: str,
        purchase_reference_id: str,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Award the admin-gated first purchase bonus exactly once.
        Safe to call from both verify and webhook paths.
        """
        status = self.get_first_purchase_bonus_status(
            userid,
            purchased_credits,
            product_id=product_id,
            current_source=purchase_source,
            current_reference_id=purchase_reference_id,
        )
        if not status.get("eligible"):
            return {"applied": False, **status}
        if self._has_prior_credit_purchase(
            userid,
            current_source=purchase_source,
            current_reference_id=purchase_reference_id,
        ):
            return {"applied": False, **status, "eligible": False, "reason": "prior_purchase_exists"}

        bonus = int(status.get("bonus_credits") or 0)
        if bonus <= 0:
            return {"applied": False, **status, "eligible": False, "reason": "zero_bonus"}

        reference_id = f"{purchase_source}:{purchase_reference_id}"
        metadata = json.dumps(
            {
                "purchase_source": purchase_source,
                "purchase_reference_id": purchase_reference_id,
                "product_id": product_id,
                "purchased_credits": int(purchased_credits),
                "percent": status.get("percent"),
                "fixed_credits": status.get("fixed_credits"),
                "max_bonus_credits": status.get("max_bonus_credits"),
                "resolved_bonus_config": status.get("resolved_bonus_config"),
                "window_minutes": status.get("window_minutes"),
                "free_question_transaction_id": status.get("free_question_transaction_id"),
            }
        )
        ok = self.add_credits(
            userid,
            bonus,
            "first_purchase_bonus",
            reference_id=reference_id,
            description=f"First purchase bonus after free question: +{bonus} credits",
            metadata=metadata,
        )
        if not ok:
            return {"applied": False, **status, "eligible": False, "reason": "bonus_write_failed"}
        return {"applied": True, **status}

    def get_purchase_discount_status(
        self,
        userid: int,
        purchased_credits: Optional[int] = None,
        *,
        product_id: Optional[str] = None,
        current_source: Optional[str] = None,
        current_reference_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return eligibility for the open purchase discount campaign (any user, no free-question gate)."""
        status = self._purchase_discount_base_status(
            userid,
            current_source=current_source,
            current_reference_id=current_reference_id,
        )
        return self._compose_bonus_status(
            status,
            purchased_credits=purchased_credits,
            product_id=product_id,
        )

    def maybe_apply_purchase_discount(
        self,
        *,
        userid: int,
        purchased_credits: int,
        purchase_source: str,
        purchase_reference_id: str,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Award the open purchase discount for an eligible verified purchase."""
        status = self.get_purchase_discount_status(
            userid,
            purchased_credits,
            product_id=product_id,
            current_source=purchase_source,
            current_reference_id=purchase_reference_id,
        )
        if not status.get("eligible"):
            return {"applied": False, **status}

        bonus = int(status.get("bonus_credits") or 0)
        if bonus <= 0:
            return {"applied": False, **status, "eligible": False, "reason": "zero_bonus"}

        reference_id = f"{purchase_source}:{purchase_reference_id}"
        metadata = json.dumps(
            {
                "purchase_source": purchase_source,
                "purchase_reference_id": purchase_reference_id,
                "product_id": product_id,
                "purchased_credits": int(purchased_credits),
                "percent": status.get("percent"),
                "fixed_credits": status.get("fixed_credits"),
                "max_bonus_credits": status.get("max_bonus_credits"),
                "resolved_bonus_config": status.get("resolved_bonus_config"),
                "window_minutes": status.get("window_minutes"),
                "window_started_at": status.get("window_started_at"),
            }
        )
        ok = self.add_credits(
            userid,
            bonus,
            "purchase_discount",
            reference_id=reference_id,
            description=f"Purchase discount: +{bonus} credits",
            metadata=metadata,
        )
        if not ok:
            return {"applied": False, **status, "eligible": False, "reason": "discount_write_failed"}
        return {"applied": True, **status}

    def apply_purchase_extras(
        self,
        *,
        userid: int,
        purchased_credits: int,
        purchase_source: str,
        purchase_reference_id: str,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply first-purchase bonus and open purchase discount for a verified purchase."""
        first_result = self.maybe_apply_first_purchase_bonus(
            userid=userid,
            purchased_credits=purchased_credits,
            purchase_source=purchase_source,
            purchase_reference_id=purchase_reference_id,
            product_id=product_id,
        )
        discount_result = self.maybe_apply_purchase_discount(
            userid=userid,
            purchased_credits=purchased_credits,
            purchase_source=purchase_source,
            purchase_reference_id=purchase_reference_id,
            product_id=product_id,
        )
        first_added = int(first_result.get("bonus_credits") or 0) if first_result.get("applied") else 0
        discount_added = int(discount_result.get("bonus_credits") or 0) if discount_result.get("applied") else 0
        return {
            "first_purchase_bonus": first_result,
            "purchase_discount": discount_result,
            "first_purchase_bonus_credits_added": first_added,
            "discount_credits_added": discount_added,
            "bonus_credits_added": first_added + discount_added,
        }

    def add_credits(self, userid: int, amount: int, source: str, reference_id: str = None, description: str = None, metadata: str = None) -> bool:
        """Add credits to user account. metadata: optional JSON (e.g. Google Play purchase_token, purchase_time for support)."""
        from db import get_conn, execute
        import logging

        log = logging.getLogger(__name__)
        try:
            with get_conn() as conn:
                current_balance = self.get_user_credits(userid)
                new_balance = current_balance + amount
                self._upsert_user_credits(conn, userid, new_balance)
                execute(
                    conn,
                    """
                    INSERT INTO credit_transactions
                    (userid, transaction_type, amount, balance_after, source, reference_id, description, metadata)
                    VALUES (?, 'earned', ?, ?, ?, ?, ?, ?)
                    """,
                    (userid, amount, new_balance, source, reference_id, description, metadata),
                )
                conn.commit()
            return True
        except Exception:
            log.exception(
                "add_credits failed userid=%s amount=%s source=%s reference_id=%s",
                userid,
                amount,
                source,
                reference_id,
            )
            return False
    
    def spend_credits(self, userid: int, amount: int, feature: str, description: str = None) -> bool:
        """Spend credits for a feature"""
        current_balance = self.get_user_credits(userid)
        
        if current_balance < amount:
            return False
        
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                new_balance = current_balance - amount
                execute(
                    conn,
                    "UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
                    (new_balance, userid),
                )
                execute(
                    conn,
                    """
                    INSERT INTO credit_transactions
                    (userid, transaction_type, amount, balance_after, source, reference_id, description)
                    VALUES (?, 'spent', ?, ?, ?, ?, ?)
                    """,
                    (userid, -amount, new_balance, "feature_usage", feature, description),
                )
                conn.commit()
            return True
        except Exception:
            return False
    
    def admin_adjust_credits(self, userid: int, amount: int, description: str = None) -> bool:
        """Admin adjustment: add (amount > 0) or deduct (amount < 0) credits. Records source 'admin_adjustment'."""
        if amount == 0:
            return True
        if amount > 0:
            return self.add_credits(userid, amount, 'admin_adjustment', None, description or "Admin adjustment")
        # amount < 0: deduct
        abs_amount = -amount
        current_balance = self.get_user_credits(userid)
        if current_balance < abs_amount:
            return False
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                new_balance = current_balance - abs_amount
                execute(
                    conn,
                    "UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
                    (new_balance, userid),
                )
                if getattr(conn.cursor(), "rowcount", 0) == 0:
                    self._upsert_user_credits(conn, userid, new_balance)
                execute(
                    conn,
                    """
                    INSERT INTO credit_transactions
                    (userid, transaction_type, amount, balance_after, source, reference_id, description)
                    VALUES (?, 'spent', ?, ?, 'admin_adjustment', NULL, ?)
                    """,
                    (userid, -abs_amount, new_balance, description or "Admin deduction"),
                )
                conn.commit()
            return True
        except Exception:
            return False

    def refund_credits(self, userid: int, amount: int, feature: str, description: str = None) -> bool:
        """Refund credits to user account"""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                current_balance = self.get_user_credits(userid)
                new_balance = current_balance + amount
                execute(
                    conn,
                    "UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
                    (new_balance, userid),
                )
                execute(
                    conn,
                    """
                    INSERT INTO credit_transactions
                    (userid, transaction_type, amount, balance_after, source, reference_id, description)
                    VALUES (?, 'refund', ?, ?, ?, ?, ?)
                    """,
                    (userid, amount, new_balance, "refund", feature, description),
                )
                conn.commit()
            return True
        except Exception:
            return False

    def is_google_play_order_reversed(self, userid: int, order_id: str) -> bool:
        """True if we already have a google_play_refund transaction for this user and order_id."""
        from db import get_conn, execute
        with get_conn() as conn:
            cursor = execute(
                conn,
                """
                SELECT 1 FROM credit_transactions
                WHERE userid = ? AND source = 'google_play_refund' AND reference_id = ?
                LIMIT 1
                """,
                (userid, order_id),
            )
            return cursor.fetchone() is not None

    def reverse_google_play_purchase(self, userid: int, order_id: str, amount: Optional[int] = None, reason: Optional[str] = None):
        """
        Reverse a Google Play credit grant (after refund via Play API or Console).
        Deducts amount (default: full original) and records a reversal.
        Idempotent: returns error if order not found or already reversed.
        reason: optional note for why the refund was issued (stored in transaction description).
        Returns: (True, amount_deducted, original_amount) or (False, error_message, None).
        """
        from db import get_conn, execute
        with get_conn() as conn:
            cur = execute(conn, """
                SELECT amount FROM credit_transactions
                WHERE userid = ? AND source = 'google_play' AND reference_id = ? AND transaction_type = 'earned'
                LIMIT 1
            """, (userid, order_id))
            row = cur.fetchone()
            if not row:
                return False, "Order not found or not a Google Play credit transaction", None

            original_amount = row[0]
            deduct = amount if amount is not None else original_amount
            if deduct <= 0 or deduct > original_amount:
                return False, "Invalid amount (must be positive and not exceed original)", None

            cur = execute(conn, """
                SELECT 1 FROM credit_transactions
                WHERE userid = ? AND source = 'google_play_refund' AND reference_id = ?
                LIMIT 1
            """, (userid, order_id))
            if cur.fetchone():
                return False, "This order was already reversed", None

            current_balance = self.get_user_credits(userid)
            # Only take back up to what the user has left
            deduct = min(deduct, current_balance)
            if deduct <= 0:
                return False, "User has no credits left to take back", None

            new_balance = current_balance - deduct
            desc = f"Reversal: Google Play refund for order {order_id}"
            if reason and reason.strip():
                desc = f"{desc}. Reason: {reason.strip()}"

            execute(conn, """
                UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?
            """, (new_balance, userid))
            execute(conn, """
                INSERT INTO credit_transactions
                (userid, transaction_type, amount, balance_after, source, reference_id, description)
                VALUES (?, 'spent', ?, ?, 'google_play_refund', ?, ?)
            """, (userid, -deduct, new_balance, order_id, desc))
            conn.commit()

            return True, deduct, original_amount

    def is_razorpay_payment_reversed(self, userid: int, payment_id: str) -> bool:
        """True if we already have a razorpay_refund transaction for this user and payment id."""
        from db import get_conn, execute

        with get_conn() as conn:
            cursor = execute(
                conn,
                """
                SELECT 1 FROM credit_transactions
                WHERE userid = ? AND source = 'razorpay_refund' AND reference_id = ?
                LIMIT 1
                """,
                (userid, payment_id),
            )
            return cursor.fetchone() is not None

    def get_razorpay_earned_snapshot(self, userid: int, payment_id: str) -> Optional[Dict[str, Any]]:
        """Original Razorpay web credit grant row for admin refund (credits + metadata)."""
        from db import get_conn, execute

        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT amount, metadata FROM credit_transactions
                WHERE userid = ? AND source = 'razorpay' AND reference_id = ? AND transaction_type = 'earned'
                LIMIT 1
                """,
                (userid, payment_id),
            )
            row = cur.fetchone()
        if not row:
            return None
        credits, metadata_json = row[0], row[1]
        amount_paise = None
        order_id = None
        product_id = None
        if metadata_json:
            try:
                meta = json.loads(metadata_json)
                amount_paise = meta.get("amount_paise")
                if amount_paise is not None:
                    try:
                        amount_paise = int(amount_paise)
                    except (TypeError, ValueError):
                        amount_paise = None
                order_id = meta.get("order_id")
                product_id = meta.get("product_id")
            except Exception:
                pass
        return {
            "credits": credits,
            "amount_paise": amount_paise,
            "order_id": order_id or "",
            "product_id": product_id or "",
        }

    def reverse_razorpay_purchase(
        self, userid: int, payment_id: str, amount: Optional[int] = None, reason: Optional[str] = None
    ):
        """
        Reverse a Razorpay web credit grant (after refund via Razorpay Dashboard or API).
        Idempotent: returns error if payment not found or already reversed.
        Returns: (True, amount_deducted, original_amount) or (False, error_message, None).
        """
        from db import get_conn, execute

        with get_conn() as conn:
            # Must use the cursor returned by execute(); conn.cursor() is a different cursor than execute()'s.
            cur = execute(
                conn,
                """
                SELECT amount FROM credit_transactions
                WHERE userid = ? AND source = 'razorpay' AND reference_id = ? AND transaction_type = 'earned'
                LIMIT 1
                """,
                (userid, payment_id),
            )
            row = cur.fetchone()
            if not row:
                return False, "Payment not found or not a Razorpay credit transaction", None

            original_amount = row[0]
            deduct = amount if amount is not None else original_amount
            if deduct <= 0 or deduct > original_amount:
                return False, "Invalid amount (must be positive and not exceed original)", None

            cur = execute(
                conn,
                """
                SELECT 1 FROM credit_transactions
                WHERE userid = ? AND source = 'razorpay_refund' AND reference_id = ?
                LIMIT 1
                """,
                (userid, payment_id),
            )
            if cur.fetchone():
                return False, "This payment was already reversed", None

            current_balance = self.get_user_credits(userid)
            deduct = min(deduct, current_balance)
            if deduct <= 0:
                return False, "User has no credits left to take back", None

            new_balance = current_balance - deduct
            desc = f"Reversal: Razorpay refund for payment {payment_id}"
            if reason and reason.strip():
                desc = f"{desc}. Reason: {reason.strip()}"

            execute(
                conn,
                """
                UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?
                """,
                (new_balance, userid),
            )
            execute(
                conn,
                """
                INSERT INTO credit_transactions
                (userid, transaction_type, amount, balance_after, source, reference_id, description)
                VALUES (?, 'spent', ?, ?, 'razorpay_refund', ?, ?)
                """,
                (userid, -deduct, new_balance, payment_id, desc),
            )
            conn.commit()

            return True, deduct, original_amount

    def redeem_promo_code(self, userid: int, code: str) -> Dict:
        """Redeem promo code for credits"""
        from db import get_conn, execute
        try:
            with get_conn() as conn:
                # Best-effort transactional safety. In Postgres this becomes a real row lock.
                execute(conn, "BEGIN")

                cur = execute(conn, """
                    SELECT id, credits, max_uses, max_uses_per_user, used_count, is_active, expires_at
                    FROM promo_codes WHERE code = ?
                """, (code,))
                promo = cur.fetchone()
            
                if not promo:
                    return {"success": False, "message": "Invalid promo code"}
            
                promo_id, credits, max_uses, max_uses_per_user, used_count, is_active, expires_at = promo
            
                if not is_active:
                    return {"success": False, "message": "Promo code is inactive"}
            
                if expires_at:
                    try:
                        exp = expires_at if isinstance(expires_at, datetime) else datetime.fromisoformat(str(expires_at))
                        if datetime.now() > exp:
                            return {"success": False, "message": "Promo code has expired"}
                    except Exception:
                        pass
            
                # Check how many times this user has used this promo code
                cur = execute(conn, """
                    SELECT COUNT(*) FROM promo_code_usage WHERE promo_code_id = ? AND userid = ?
                """, (promo_id, userid))
                user_usage_count = cur.fetchone()[0]
            
                if user_usage_count >= max_uses_per_user:
                    return {"success": False, "message": f"You have already used this promo code {max_uses_per_user} time(s)"}
            
                # Record usage first
                execute(conn, """
                    INSERT INTO promo_code_usage (promo_code_id, userid, credits_earned)
                    VALUES (?, ?, ?)
                """, (promo_id, userid, credits))
            
                # Update user credits directly in this transaction
                current_balance = self.get_user_credits(userid)
                new_balance = current_balance + credits
            
                self._upsert_user_credits(conn, userid, new_balance)
            
                execute(conn, """
                    INSERT INTO credit_transactions
                    (userid, transaction_type, amount, balance_after, source, reference_id, description)
                    VALUES (?, 'earned', ?, ?, ?, ?, ?)
                """, (userid, credits, new_balance, 'promo_code', code, f"Promo code: {code}"))
            
                # Update promo code usage count
                execute(conn, "UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?", (promo_id,))
            
                conn.commit()
            
                return {
                    "success": True,
                    "message": f"Successfully redeemed {credits} credits!",
                    "credits_earned": credits,
                }
        except Exception as e:
            print(f"Error in redeem_promo_code: {str(e)}")
            return {"success": False, "message": "An error occurred while redeeming the promo code"}
    
    def get_credit_setting(self, setting_key: str) -> int:
        """Get effective credit cost (discount if set, else setting_value). Used for deduction."""
        effective, _, _ = self.get_credit_setting_and_original(setting_key)
        return effective

    def get_credit_setting_and_original(self, setting_key: str) -> tuple:
        """Returns (effective_cost, original_value, discount_value). discount_value is None if no discount."""
        from db import get_conn, execute
        with get_conn() as conn:
            cursor = execute(
                conn,
                "SELECT setting_value, discount FROM credit_settings WHERE setting_key = ?",
                (setting_key,),
            )
            result = cursor.fetchone()
        if not result:
            return (1, 1, None)
        value = result[0]
        discount = result[1] if len(result) > 1 else None
        effective = discount if (discount is not None and discount >= 0) else value
        return (effective, value, discount)
    
    def update_credit_setting(self, setting_key: str, value: int, discount: Any = _DISCOUNT_OMIT) -> bool:
        """Update credit cost setting. discount=_DISCOUNT_OMIT: leave discount column unchanged; None: set to NULL; int: set value."""
        from db import get_conn, execute
        with get_conn() as conn:
            if discount is _DISCOUNT_OMIT:
                cursor = execute(
                    conn,
                    """
                    UPDATE credit_settings
                    SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE setting_key = ?
                    """,
                    (value, setting_key),
                )
            else:
                d = None if discount is None or discount < 0 else int(discount)
                cursor = execute(
                    conn,
                    """
                    UPDATE credit_settings
                    SET setting_value = ?, discount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE setting_key = ?
                    """,
                    (value, d, setting_key),
                )
            success = (cursor.rowcount or 0) > 0
            conn.commit()
            return success
    
    def get_all_credit_settings(self) -> List[Dict]:
        """Get all credit settings (value = original cost, discount = discounted cost when set)."""
        from db import get_conn, execute
        keys = (
            'chat_question_cost', 'instant_chat_cost', 'speech_chat_cost', 'premium_chat_cost', 'partnership_analysis_cost', 'wealth_analysis_cost',
            'marriage_analysis_cost', 'health_analysis_cost', 'education_analysis_cost', 'career_analysis_cost',
            'progeny_analysis_cost', 'trading_daily_cost', 'trading_monthly_cost', 'childbirth_planner_cost',
            'vehicle_purchase_cost', 'griha_pravesh_cost', 'gold_purchase_cost', 'business_opening_cost',
            'event_timeline_cost', 'karma_analysis_cost', 'ashtakavarga_life_predictions_cost', 'podcast_cost'
        )
        placeholders = ", ".join(["?"] * len(keys))
        with get_conn() as conn:
            cursor = execute(
                conn,
                f"""
                SELECT setting_key, setting_value, description, discount
                FROM credit_settings
                WHERE setting_key IN ({placeholders})
                ORDER BY setting_key
                """,
                keys,
            )
            rows = cursor.fetchall()
            settings = []
            for row in rows:
                settings.append({
                    "key": row[0],
                    "value": row[1],
                    "description": row[2],
                    "discount": row[3] if len(row) > 3 else None,
                })
            # Ensure speech_chat_cost exists so admin Feature Costs always shows it
            if not any(s["key"] == "speech_chat_cost" for s in settings):
                try:
                    execute(
                        conn,
                        """
                        INSERT INTO credit_settings (setting_key, setting_value, description)
                        VALUES ('speech_chat_cost', 1, 'Credits per speech chat turn (Tara / voice-first)')
                        """,
                    )
                    conn.commit()
                    settings.append({
                        "key": "speech_chat_cost",
                        "value": 1,
                        "description": "Credits per speech chat turn (Tara / voice-first)",
                        "discount": None,
                    })
                except Exception:
                    pass
            # Ensure podcast_cost exists so admin Feature Costs always shows it
            if not any(s["key"] == "podcast_cost" for s in settings):
                try:
                    execute(
                        conn,
                        """
                        INSERT INTO credit_settings (setting_key, setting_value, description)
                        VALUES ('podcast_cost', 2, 'Credits per podcast (listen to message as audio)')
                        """,
                    )
                    conn.commit()
                    settings.append({
                        "key": "podcast_cost",
                        "value": 2,
                        "description": "Credits per podcast (listen to message as audio)",
                        "discount": None,
                    })
                except Exception:
                    pass
            return settings
    
    def get_transaction_history(
        self,
        userid: int,
        limit: int = 50,
        *,
        exclude_zero_amount: bool = False,
        ledger_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get credit transaction history for user. reference_id is the activity/feature for spends.
        ledger_filter: None (all), 'purchases' (earned + refund credits in), 'spend' (spent rows only).
        """
        from db import get_conn, execute
        zero_filter = " AND amount <> 0" if exclude_zero_amount else ""
        lf = (ledger_filter or "").strip().lower()
        type_filter = ""
        if lf == "purchases":
            type_filter = " AND transaction_type IN ('earned', 'refund')"
        elif lf == "spend":
            type_filter = " AND transaction_type = 'spent'"
        with get_conn() as conn:
            cursor = execute(conn, f"""
                SELECT id, transaction_type, amount, balance_after, source, reference_id, description, created_at
                FROM credit_transactions
                WHERE userid = ?{zero_filter}{type_filter}
                ORDER BY created_at DESC
                LIMIT ?
            """, (userid, limit))
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    "id": row[0],
                    "type": row[1],
                    "amount": row[2],
                    "balance_after": row[3],
                    "source": row[4],
                    "reference_id": row[5],
                    "description": row[6],
                    "date": row[7],
                })
            return transactions

    def get_daily_activity(self, target_date: str) -> List[Dict]:
        """
        Get all credit transactions for a given date (YYYY-MM-DD) across all users.
        Returns list with user info and transaction details, ordered by time (newest first).
        """
        from db import get_conn, execute
        # date() works in both sqlite and postgres
        with get_conn() as conn:
            cursor = execute(conn, """
                SELECT ct.id, ct.userid, u.name, u.phone,
                       ct.transaction_type, ct.amount, ct.balance_after,
                       ct.source, ct.reference_id, ct.description, ct.created_at
                FROM credit_transactions ct
                LEFT JOIN users u ON u.userid = ct.userid
                WHERE date(ct.created_at) = ?
                ORDER BY ct.created_at DESC
            """, (target_date,))
            rows = cursor.fetchall()

        transactions = []
        for row in rows:
            transactions.append({
                "id": row[0],
                "userid": row[1],
                "user_name": row[2] or "",
                "user_phone": row[3] or "",
                "type": row[4],
                "amount": row[5],
                "balance_after": row[6],
                "source": row[7],
                "reference_id": row[8],
                "description": row[9],
                "created_at": row[10],
            })
        return transactions

    def search_transactions(
        self,
        from_date: str,
        to_date: str,
        query: Optional[str] = None,
        limit: int = 500,
        *,
        exclude_zero_amount: bool = False,
    ) -> List[Dict]:
        """
        Search credit transactions across all users for a date range, with optional
        wildcard search on user name or phone. Dates are YYYY-MM-DD inclusive.
        """
        from db import get_conn, execute

        zero_filter = " AND ct.amount <> 0" if exclude_zero_amount else ""
        sql = f"""
            SELECT ct.id, ct.userid, u.name, u.phone,
                   ct.transaction_type, ct.amount, ct.balance_after,
                   ct.source, ct.reference_id, ct.description, ct.created_at
            FROM credit_transactions ct
            LEFT JOIN users u ON u.userid = ct.userid
            WHERE date(ct.created_at) >= ? AND date(ct.created_at) <= ?{zero_filter}
        """
        params: List[Any] = [from_date, to_date]

        if query and query.strip():
            like = f"%{query.strip()}%"
            # ILIKE matches SQLite-style case-insensitive search better for names/phones
            sql += " AND (u.name ILIKE ? OR u.phone ILIKE ?)"
            params.extend([like, like])

        sql += " ORDER BY ct.created_at DESC LIMIT ?"
        params.append(limit)

        with get_conn() as conn:
            cur = execute(conn, sql, params)
            rows = cur.fetchall()

        transactions = []
        for row in rows:
            transactions.append({
                "id": row[0],
                "userid": row[1],
                "user_name": row[2] or "",
                "user_phone": row[3] or "",
                "type": row[4],
                "amount": row[5],
                "balance_after": row[6],
                "source": row[7],
                "reference_id": row[8],
                "description": row[9],
                "created_at": row[10],
            })
        return transactions

    def get_search_transaction_summary(
        self,
        from_date: str,
        to_date: str,
        query: Optional[str] = None,
        *,
        exclude_zero_amount: bool = False,
    ) -> Dict[str, int]:
        """
        Backend summary for admin credit ledger over the exact same filter as search_transactions.
        Keeps admin UI totals accurate without relying on whatever row limit is shown in the page.
        """
        from db import get_conn, execute

        range_start = f"{from_date} 00:00:00"
        range_end_exclusive_sql = f"CAST(? AS DATE) + INTERVAL '1 day'"
        zero_filter = " AND ct.amount <> 0" if exclude_zero_amount else ""
        query_filter = ""
        params: List[Any] = [range_start, to_date]
        if query and query.strip():
            like = f"%{query.strip()}%"
            query_filter = " AND (u.name ILIKE ? OR u.phone ILIKE ?)"
            params.extend([like, like])

        sql = f"""
            SELECT
                COALESCE(SUM(CASE
                    WHEN ct.source IN ('google_play', 'razorpay')
                     AND ct.transaction_type IN ('earned', 'refund')
                    THEN ABS(ct.amount) ELSE 0 END), 0) AS purchased_credits,
                COALESCE(SUM(CASE
                    WHEN ct.transaction_type = 'spent'
                     AND ct.source NOT IN ('admin_adjustment', 'google_play_refund', 'razorpay_refund', 'refund')
                    THEN ABS(ct.amount) ELSE 0 END), 0) AS user_spend_credits,
                COALESCE(SUM(CASE
                    WHEN ct.source = 'admin_adjustment'
                     AND ct.transaction_type IN ('earned', 'refund')
                    THEN ABS(ct.amount) ELSE 0 END), 0) AS admin_added_credits,
                COALESCE(SUM(CASE
                    WHEN ct.source = 'admin_adjustment'
                     AND ct.transaction_type = 'spent'
                    THEN ABS(ct.amount) ELSE 0 END), 0) AS admin_deducted_credits,
                COALESCE(SUM(CASE
                    WHEN ct.transaction_type = 'refund'
                      OR ct.source IN ('google_play_refund', 'razorpay_refund', 'refund')
                    THEN ABS(ct.amount) ELSE 0 END), 0) AS refund_reversal_credits,
                COALESCE(SUM(CASE
                    WHEN ct.transaction_type = 'spent'
                     AND ct.source = 'feature_usage'
                     AND ct.reference_id = 'chat_question'
                     AND ct.amount = 0
                    THEN 1 ELSE 0 END), 0) AS free_questions_count
            FROM credit_transactions ct
            LEFT JOIN users u ON u.userid = ct.userid
            WHERE ct.created_at >= ?
              AND ct.created_at < {range_end_exclusive_sql}
              {zero_filter}
              {query_filter}
        """

        with get_conn() as conn:
            cur = execute(conn, sql, params)
            row = cur.fetchone() or (0, 0, 0, 0, 0, 0)

        return {
            "purchased_credits": int(row[0] or 0),
            "user_spend_credits": int(row[1] or 0),
            "admin_added_credits": int(row[2] or 0),
            "admin_deducted_credits": int(row[3] or 0),
            "refund_reversal_credits": int(row[4] or 0),
            "free_questions_count": int(row[5] or 0),
        }

    def get_google_play_transactions(
        self,
        from_date: str,
        to_date: str,
        query: Optional[str] = None,
        order_id_filter: Optional[str] = None,
        currency_filter: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        List Google Play credit transactions (source='google_play') with user info,
        purchase_token from metadata, and status (Credited / Reversed).
        Reversed = exists a row with source='google_play_refund' and same userid + reference_id.
        """
        from db import get_conn, execute
        with get_conn() as conn:
            sql = """
            SELECT ct.id, ct.userid, u.name, u.phone,
                   ct.reference_id, ct.amount, ct.metadata, ct.created_at
            FROM credit_transactions ct
            LEFT JOIN users u ON u.userid = ct.userid
            WHERE ct.source = 'google_play'
              AND ct.transaction_type = 'earned'
              AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
            """
            params: List[Any] = [from_date, to_date]
            if query and query.strip():
                like = f"%{query.strip()}%"
                sql += " AND (u.name ILIKE ? OR u.phone ILIKE ?)"
                params.extend([like, like])
            if order_id_filter and order_id_filter.strip():
                sql += " AND ct.reference_id ILIKE ?"
                params.append(f"%{order_id_filter.strip()}%")
            sql += " ORDER BY ct.created_at DESC LIMIT ?"
            params.append(limit)
            cur = execute(conn, sql, params)
            rows = cur.fetchall()

            # (userid, order_id) -> total reversed amount (for partial display)
            reversed_amounts = {}
            cur_rev = execute(
                conn,
                """
                SELECT userid, reference_id, SUM(ABS(amount)) FROM credit_transactions
                WHERE source = 'google_play_refund' AND reference_id IS NOT NULL
                GROUP BY userid, reference_id
                """,
                (),
            )
            for r in cur_rev.fetchall():
                reversed_amounts[(r[0], r[1])] = r[2]
            out = []
            normalized_currency = (currency_filter or "").strip().upper()
            for row in rows:
                tx_id, userid, name, phone, order_id, amount, metadata_json, created_at = row
                purchase_token = ""
                price_amount_micros = None
                price_currency = None
                localized_price = None
                if metadata_json:
                    try:
                        meta = json.loads(metadata_json)
                        purchase_token = meta.get("purchase_token") or ""
                        price_amount_micros = meta.get("price_amount_micros")
                        price_currency = meta.get("price_currency")
                        localized_price = meta.get("localized_price")
                    except Exception:
                        pass
                key = (userid, order_id)
                reversed_amt = reversed_amounts.get(key, 0)
                status = "Reversed" if reversed_amt else "Credited"
                if normalized_currency:
                    tx_currency = (price_currency or "").strip().upper()
                    if tx_currency != normalized_currency:
                        continue
                out.append({
                    "id": tx_id,
                    "userid": userid,
                    "user_name": name or "",
                    "user_phone": phone or "",
                    "order_id": order_id or "",
                    "purchase_token": purchase_token,
                    "amount": amount,
                    "created_at": created_at,
                    "status": status,
                    "reversed_amount": reversed_amt if reversed_amt else None,
                    "price_amount_micros": price_amount_micros,
                    "price_currency": price_currency,
                    "localized_price": localized_price,
                })
            return out

    def get_razorpay_transactions(
        self,
        from_date: str,
        to_date: str,
        query: Optional[str] = None,
        payment_id_filter: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        List Razorpay web credit transactions (source='razorpay') with user info and reversal status.
        """
        from db import get_conn, execute

        with get_conn() as conn:
            # Join reversal totals in SQL with TRIM(reference_id) so earned vs refund rows always
            # match (avoids Python dict key misses from whitespace / type quirks).
            sql = """
            SELECT ct.id, ct.userid, u.name, u.phone,
                   ct.reference_id, ct.amount, ct.metadata, ct.created_at,
                   COALESCE(rev.rev_sum, 0) AS reversed_amt
            FROM credit_transactions ct
            LEFT JOIN users u ON u.userid = ct.userid
            LEFT JOIN (
                SELECT userid,
                       TRIM(BOTH FROM COALESCE(reference_id, '')) AS ref_trim,
                       SUM(ABS(amount))::bigint AS rev_sum
                FROM credit_transactions
                WHERE source = 'razorpay_refund'
                  AND reference_id IS NOT NULL
                  AND TRIM(BOTH FROM COALESCE(reference_id, '')) <> ''
                GROUP BY userid, TRIM(BOTH FROM COALESCE(reference_id, ''))
            ) rev ON rev.userid = ct.userid
               AND TRIM(BOTH FROM COALESCE(ct.reference_id, '')) = rev.ref_trim
            WHERE ct.source = 'razorpay'
              AND ct.transaction_type = 'earned'
              AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
            """
            params: List[Any] = [from_date, to_date]
            if query and query.strip():
                like = f"%{query.strip()}%"
                sql += " AND (u.name ILIKE ? OR u.phone ILIKE ?)"
                params.extend([like, like])
            if payment_id_filter and payment_id_filter.strip():
                sql += " AND ct.reference_id ILIKE ?"
                params.append(f"%{payment_id_filter.strip()}%")
            sql += " ORDER BY ct.created_at DESC LIMIT ?"
            params.append(limit)
            cur = execute(conn, sql, params)
            rows = cur.fetchall()

            out: List[Dict[str, Any]] = []
            for row in rows:
                tx_id, userid, name, phone, pay_id, amount, metadata_json, created_at, reversed_raw = row
                try:
                    reversed_amt = int(reversed_raw or 0)
                except (TypeError, ValueError):
                    reversed_amt = 0
                order_id = ""
                amount_paise = None
                currency = None
                product_id = None
                if metadata_json:
                    try:
                        meta = json.loads(metadata_json)
                        order_id = meta.get("order_id") or ""
                        ap = meta.get("amount_paise")
                        if ap is not None:
                            try:
                                amount_paise = int(ap)
                            except (TypeError, ValueError):
                                amount_paise = None
                        currency = meta.get("currency")
                        product_id = meta.get("product_id")
                    except Exception:
                        pass
                status = "Reversed" if reversed_amt > 0 else "Credited"
                out.append(
                    {
                        "id": tx_id,
                        "userid": userid,
                        "user_name": name or "",
                        "user_phone": phone or "",
                        "payment_id": (pay_id or "").strip(),
                        "order_id": order_id,
                        "amount": amount,
                        "amount_paise": amount_paise,
                        "currency": currency or "INR",
                        "product_id": product_id or "",
                        "created_at": created_at,
                        "status": status,
                        "reversed_amount": reversed_amt if reversed_amt > 0 else None,
                    }
                )
            return out

    def get_dashboard_stats(self, from_date: str, to_date: str) -> Dict:
        """
        Aggregate stats for admin dashboard: top users by activity count,
        distribution by activity (reference_id), and daily time series.
        from_date, to_date: YYYY-MM-DD inclusive.
        """
        from db import get_conn, execute
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT ct.userid, u.name, u.phone, COUNT(*) AS cnt
                FROM credit_transactions ct
                LEFT JOIN users u ON u.userid = ct.userid
                WHERE ct.transaction_type = 'spent'
                  AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
                GROUP BY ct.userid, u.name, u.phone
                ORDER BY cnt DESC
                LIMIT 10
                """,
                (from_date, to_date),
            )
            top_users = [
                {"userid": r[0], "user_name": r[1] or "", "user_phone": r[2] or "", "transaction_count": r[3]}
                for r in cur.fetchall()
            ]
            top_userids = {u["userid"] for u in top_users}

            cur = execute(
                conn,
                """
                SELECT ct.userid, COALESCE(ct.reference_id, 'other') AS activity, COUNT(*) AS cnt
                FROM credit_transactions ct
                WHERE ct.transaction_type = 'spent'
                  AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
                GROUP BY ct.userid, COALESCE(ct.reference_id, 'other')
                """,
                (from_date, to_date),
            )
            activity_breakdown = {}
            for row in cur.fetchall():
                uid, activity, cnt = row[0], row[1], row[2]
                if uid in top_userids:
                    if uid not in activity_breakdown:
                        activity_breakdown[uid] = []
                    activity_breakdown[uid].append({"activity": activity, "count": cnt})

            for u in top_users:
                u["by_activity"] = activity_breakdown.get(u["userid"], [])

            cur = execute(
                conn,
                """
                SELECT COALESCE(ct.reference_id, 'other') AS activity,
                       COUNT(*) AS cnt,
                       SUM(-ct.amount) AS total_credits
                FROM credit_transactions ct
                WHERE ct.transaction_type = 'spent'
                  AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
                GROUP BY COALESCE(ct.reference_id, 'other')
                ORDER BY total_credits DESC
                """,
                (from_date, to_date),
            )
            distribution = [
                {"activity": r[0], "transaction_count": r[1], "total_credits": r[2] or 0}
                for r in cur.fetchall()
            ]

            cur = execute(
                conn,
                """
                SELECT date(ct.created_at) AS d,
                       SUM(CASE WHEN ct.transaction_type IN ('earned', 'refund') THEN ct.amount ELSE 0 END) AS earned,
                       SUM(CASE WHEN ct.transaction_type = 'spent' THEN -ct.amount ELSE 0 END) AS spent,
                       COUNT(*) AS transaction_count
                FROM credit_transactions ct
                WHERE date(ct.created_at) >= ? AND date(ct.created_at) <= ?
                GROUP BY date(ct.created_at)
                ORDER BY d
                """,
                (from_date, to_date),
            )
            time_series = [
                {"date": r[0], "earned": r[1] or 0, "spent": r[2] or 0, "transaction_count": r[3]}
                for r in cur.fetchall()
            ]

            cur = execute(
                conn,
                """
                SELECT
                    SUM(CASE WHEN transaction_type IN ('earned', 'refund') THEN amount ELSE 0 END),
                    SUM(CASE WHEN transaction_type = 'spent' THEN -amount ELSE 0 END),
                    COUNT(*)
                FROM credit_transactions
                WHERE date(created_at) >= ? AND date(created_at) <= ?
                """,
                (from_date, to_date),
            )
            row = cur.fetchone()
            total_earned = row[0] or 0
            total_spent = row[1] or 0
            total_count = row[2] or 0

        return {
            "from_date": from_date,
            "to_date": to_date,
            "summary": {
                "total_earned": total_earned,
                "total_spent": total_spent,
                "transaction_count": total_count,
            },
            "top_users_by_activity": top_users,
            "distribution_by_activity": distribution,
            "time_series": time_series,
        }

    def get_admin_intelligence_stats(self, from_date: str, to_date: str) -> Dict:
        from db import get_conn, execute

        paid_sources = ("google_play", "razorpay")
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                WITH range_tx AS (
                    SELECT userid, transaction_type, amount, source, reference_id, created_at
                    FROM credit_transactions
                    WHERE date(created_at) >= ? AND date(created_at) <= ?
                ),
                paid_tx AS (
                    SELECT *
                    FROM range_tx
                    WHERE transaction_type = 'earned'
                      AND source IN (?, ?)
                ),
                spent_tx AS (
                    SELECT *
                    FROM range_tx
                    WHERE transaction_type = 'spent'
                ),
                prior_payers AS (
                    SELECT DISTINCT userid
                    FROM credit_transactions
                    WHERE transaction_type = 'earned'
                      AND source IN (?, ?)
                      AND date(created_at) < ?
                )
                SELECT
                    COALESCE((SELECT SUM(amount) FROM paid_tx), 0) AS paid_credits,
                    COALESCE((SELECT SUM(-amount) FROM spent_tx), 0) AS spent_credits,
                    COALESCE((SELECT COUNT(*) FROM paid_tx), 0) AS purchase_count,
                    COALESCE((SELECT COUNT(DISTINCT userid) FROM paid_tx), 0) AS unique_payers,
                    COALESCE((SELECT COUNT(*) FROM (SELECT userid FROM paid_tx GROUP BY userid HAVING COUNT(*) >= 2) t), 0) AS repeat_payers,
                    COALESCE((SELECT COUNT(*) FROM (SELECT p.userid FROM paid_tx p LEFT JOIN prior_payers pp ON pp.userid = p.userid WHERE pp.userid IS NULL GROUP BY p.userid) t), 0) AS first_time_payers,
                    COALESCE((SELECT SUM(credits) FROM user_credits), 0) AS current_wallet_credits,
                    COALESCE((SELECT COUNT(*) FROM user_credits WHERE credits > 0), 0) AS users_with_balance
                """,
                (from_date, to_date, *paid_sources, *paid_sources, from_date),
            )
            row = cur.fetchone() or (0, 0, 0, 0, 0, 0, 0, 0)
            summary = {
                "paid_credits": row[0] or 0,
                "spent_credits": row[1] or 0,
                "purchase_count": row[2] or 0,
                "unique_payers": row[3] or 0,
                "repeat_payers": row[4] or 0,
                "first_time_payers": row[5] or 0,
                "current_wallet_credits": row[6] or 0,
                "users_with_balance": row[7] or 0,
            }

            cur = execute(
                conn,
                """
                SELECT
                    source,
                    COUNT(*) AS purchase_count,
                    COUNT(DISTINCT userid) AS unique_users,
                    COALESCE(SUM(amount), 0) AS credits
                FROM credit_transactions
                WHERE transaction_type = 'earned'
                  AND source IN (?, ?)
                  AND date(created_at) >= ? AND date(created_at) <= ?
                GROUP BY source
                ORDER BY credits DESC, purchase_count DESC
                """,
                (*paid_sources, from_date, to_date),
            )
            purchase_sources = [
                {
                    "source": r[0],
                    "purchase_count": r[1] or 0,
                    "unique_users": r[2] or 0,
                    "credits": r[3] or 0,
                }
                for r in cur.fetchall()
            ]

            cur = execute(
                conn,
                """
                SELECT
                    COALESCE(reference_id, 'other') AS feature,
                    COUNT(*) AS spend_count,
                    COUNT(DISTINCT userid) AS unique_users,
                    COALESCE(SUM(-amount), 0) AS spent_credits,
                    ROUND(AVG(-amount)::numeric, 2) AS avg_credits
                FROM credit_transactions
                WHERE transaction_type = 'spent'
                  AND date(created_at) >= ? AND date(created_at) <= ?
                GROUP BY COALESCE(reference_id, 'other')
                ORDER BY spent_credits DESC, spend_count DESC
                LIMIT 15
                """,
                (from_date, to_date),
            )
            spend_by_feature = [
                {
                    "feature": r[0],
                    "spend_count": r[1] or 0,
                    "unique_users": r[2] or 0,
                    "spent_credits": r[3] or 0,
                    "avg_credits": float(r[4] or 0),
                }
                for r in cur.fetchall()
            ]

            cur = execute(
                conn,
                """
                WITH paid_range AS (
                    SELECT userid, amount, source, created_at
                    FROM credit_transactions
                    WHERE transaction_type = 'earned'
                      AND source IN (?, ?)
                      AND date(created_at) >= ? AND date(created_at) <= ?
                ),
                spent_range AS (
                    SELECT userid, COUNT(*) AS spend_count, COALESCE(SUM(-amount), 0) AS spent_credits
                    FROM credit_transactions
                    WHERE transaction_type = 'spent'
                      AND date(created_at) >= ? AND date(created_at) <= ?
                    GROUP BY userid
                ),
                payer_rollup AS (
                    SELECT
                        p.userid,
                        COUNT(*) AS purchase_count,
                        COALESCE(SUM(p.amount), 0) AS purchased_credits,
                        MIN(p.created_at) AS first_purchase_at,
                        MAX(p.created_at) AS last_purchase_at,
                        (
                            SELECT p2.source
                            FROM paid_range p2
                            WHERE p2.userid = p.userid
                            GROUP BY p2.source
                            ORDER BY SUM(p2.amount) DESC, COUNT(*) DESC, p2.source
                            LIMIT 1
                        ) AS primary_source
                    FROM paid_range p
                    GROUP BY p.userid
                )
                SELECT
                    pr.userid,
                    COALESCE(u.name, '') AS user_name,
                    COALESCE(u.phone, '') AS user_phone,
                    pr.purchase_count,
                    pr.purchased_credits,
                    COALESCE(sr.spent_credits, 0) AS spent_credits,
                    COALESCE(sr.spend_count, 0) AS spend_count,
                    COALESCE(uc.credits, 0) AS current_balance,
                    pr.primary_source,
                    pr.first_purchase_at,
                    pr.last_purchase_at
                FROM payer_rollup pr
                LEFT JOIN spent_range sr ON sr.userid = pr.userid
                LEFT JOIN users u ON u.userid = pr.userid
                LEFT JOIN user_credits uc ON uc.userid = pr.userid
                ORDER BY pr.purchased_credits DESC, pr.purchase_count DESC, pr.last_purchase_at DESC
                LIMIT 50
                """,
                (*paid_sources, from_date, to_date, from_date, to_date),
            )
            top_payers = [
                {
                    "userid": r[0],
                    "user_name": r[1],
                    "user_phone": r[2],
                    "purchase_count": r[3] or 0,
                    "purchased_credits": r[4] or 0,
                    "spent_credits": r[5] or 0,
                    "spend_count": r[6] or 0,
                    "current_balance": r[7] or 0,
                    "primary_source": r[8] or "",
                    "first_purchase_at": r[9].isoformat() if r[9] else None,
                    "last_purchase_at": r[10].isoformat() if r[10] else None,
                }
                for r in cur.fetchall()
            ]

            cur = execute(
                conn,
                """
                SELECT bucket, user_count, total_credits
                FROM (
                    SELECT
                        CASE
                            WHEN credits <= 0 THEN '0'
                            WHEN credits BETWEEN 1 AND 49 THEN '1-49'
                            WHEN credits BETWEEN 50 AND 199 THEN '50-199'
                            WHEN credits BETWEEN 200 AND 499 THEN '200-499'
                            WHEN credits BETWEEN 500 AND 999 THEN '500-999'
                            ELSE '1000+'
                        END AS bucket,
                        COUNT(*) AS user_count,
                        SUM(credits) AS total_credits,
                        CASE
                            WHEN credits <= 0 THEN 0
                            WHEN credits BETWEEN 1 AND 49 THEN 1
                            WHEN credits BETWEEN 50 AND 199 THEN 2
                            WHEN credits BETWEEN 200 AND 499 THEN 3
                            WHEN credits BETWEEN 500 AND 999 THEN 4
                            ELSE 5
                        END AS bucket_order
                    FROM user_credits
                    GROUP BY bucket, bucket_order
                ) buckets
                ORDER BY bucket_order
                """,
            )
            wallet_buckets = [
                {"bucket": r[0], "user_count": r[1] or 0, "total_credits": r[2] or 0}
                for r in cur.fetchall()
            ]

            cur = execute(
                conn,
                """
                WITH paid_range AS (
                    SELECT userid, SUM(amount) AS purchased_credits, MAX(created_at) AS last_purchase_at
                    FROM credit_transactions
                    WHERE transaction_type = 'earned'
                      AND source IN (?, ?)
                      AND date(created_at) >= ? AND date(created_at) <= ?
                    GROUP BY userid
                ),
                spent_range AS (
                    SELECT userid, SUM(-amount) AS spent_credits
                    FROM credit_transactions
                    WHERE transaction_type = 'spent'
                      AND date(created_at) >= ? AND date(created_at) <= ?
                    GROUP BY userid
                )
                SELECT
                    p.userid,
                    COALESCE(u.name, '') AS user_name,
                    COALESCE(u.phone, '') AS user_phone,
                    p.purchased_credits,
                    COALESCE(s.spent_credits, 0) AS spent_credits,
                    COALESCE(uc.credits, 0) AS current_balance,
                    p.last_purchase_at
                FROM paid_range p
                LEFT JOIN spent_range s ON s.userid = p.userid
                LEFT JOIN users u ON u.userid = p.userid
                LEFT JOIN user_credits uc ON uc.userid = p.userid
                WHERE COALESCE(s.spent_credits, 0) = 0
                   OR COALESCE(uc.credits, 0) >= 200
                ORDER BY current_balance DESC, p.purchased_credits DESC, p.last_purchase_at DESC
                LIMIT 25
                """,
                (*paid_sources, from_date, to_date, from_date, to_date),
            )
            dormant_balances = [
                {
                    "userid": r[0],
                    "user_name": r[1],
                    "user_phone": r[2],
                    "purchased_credits": r[3] or 0,
                    "spent_credits": r[4] or 0,
                    "current_balance": r[5] or 0,
                    "last_purchase_at": r[6].isoformat() if r[6] else None,
                }
                for r in cur.fetchall()
            ]

            cur = execute(
                conn,
                """
                WITH daily_paid AS (
                    SELECT
                        date(created_at) AS day,
                        source,
                        SUM(amount) AS credits
                    FROM credit_transactions
                    WHERE transaction_type = 'earned'
                      AND source IN (?, ?)
                      AND date(created_at) >= ? AND date(created_at) <= ?
                    GROUP BY date(created_at), source
                ),
                daily_spent AS (
                    SELECT
                        date(created_at) AS day,
                        SUM(-amount) AS spent_credits
                    FROM credit_transactions
                    WHERE transaction_type = 'spent'
                      AND date(created_at) >= ? AND date(created_at) <= ?
                    GROUP BY date(created_at)
                )
                SELECT
                    COALESCE(p.day, s.day) AS day,
                    COALESCE(SUM(CASE WHEN p.source = 'google_play' THEN p.credits ELSE 0 END), 0) AS google_play_credits,
                    COALESCE(SUM(CASE WHEN p.source = 'razorpay' THEN p.credits ELSE 0 END), 0) AS razorpay_credits,
                    COALESCE(MAX(s.spent_credits), 0) AS spent_credits
                FROM daily_paid p
                FULL OUTER JOIN daily_spent s ON s.day = p.day
                GROUP BY COALESCE(p.day, s.day)
                ORDER BY day
                """,
                (*paid_sources, from_date, to_date, from_date, to_date),
            )
            time_series = [
                {
                    "date": r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0]),
                    "google_play_credits": r[1] or 0,
                    "razorpay_credits": r[2] or 0,
                    "spent_credits": r[3] or 0,
                }
                for r in cur.fetchall()
            ]

        return {
            "from_date": from_date,
            "to_date": to_date,
            "summary": summary,
            "purchase_sources": purchase_sources,
            "spend_by_feature": spend_by_feature,
            "top_payers": top_payers,
            "wallet_buckets": wallet_buckets,
            "dormant_balances": dormant_balances,
            "time_series": time_series,
        }
