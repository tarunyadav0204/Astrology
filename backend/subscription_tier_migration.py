"""
Subscription tier migration: ensure subscription_plans and user_subscriptions exist,
add tier columns (tier_name, discount_percent, google_play_product_id), and seed VIP plans.
Backward compatible: only adds columns and inserts new rows; does not drop or rename existing data.
"""
import sqlite3
import os

DB_PATH = os.environ.get("ASTROLOGY_DB_PATH", "astrology.db")
PLATFORM_ASTROROSHNI = "astroroshni"


def ensure_subscription_tier_schema(db_path: str = None) -> None:
    db_path = db_path or DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # 1) Create subscription_plans if not exist (new installs get full schema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscription_plans (
                plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                price DECIMAL(10,2) DEFAULT 0.00,
                duration_months INTEGER DEFAULT 1,
                features TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tier_name TEXT,
                discount_percent INTEGER DEFAULT 0,
                google_play_product_id TEXT
            )
        """)
        # 2) Do not create user_subscriptions here - existing DBs may use subscription_id as PK column;
        #    main.py expects us.subscription_id. New installs should run full init or a separate migration.

        # 3) Add new columns to subscription_plans if missing (existing DBs)
        for col_def in [
            ("tier_name", "TEXT"),
            ("discount_percent", "INTEGER DEFAULT 0"),
            ("google_play_product_id", "TEXT"),
        ]:
            col_name, col_type = col_def
            try:
                cursor.execute(
                    f"ALTER TABLE subscription_plans ADD COLUMN {col_name} {col_type}"
                )
            except sqlite3.OperationalError:
                pass  # column already exists

        conn.commit()

        # 4) Seed Free plan for astroroshni if not present (register flow needs it)
        cursor.execute(
            "SELECT plan_id FROM subscription_plans WHERE platform = ? AND plan_name = ?",
            (PLATFORM_ASTROROSHNI, "Free"),
        )
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO subscription_plans (platform, plan_name, price, duration_months, features, is_active, tier_name, discount_percent, google_play_product_id)
                VALUES (?, 'Free', 0.00, 12, '{"basic": true}', 1, 'Free', 0, NULL)
            """, (PLATFORM_ASTROROSHNI,))
            conn.commit()

        # 5) Seed VIP tier plans if not present (explicit names; same discount for all features).
        # Product IDs are tier-based, not price-based: you set actual price in Google Play Console and/or subscription_plans.price.
        vip_plans = [
            ("VIP Silver", 10, "subscription_vip_silver", 400.00),
            ("VIP Gold", 20, "subscription_vip_gold", 500.00),
            ("VIP Platinum", 30, "subscription_vip_platinum", 600.00),
        ]
        for tier_name, discount_percent, product_id, price in vip_plans:
            cursor.execute(
                "SELECT plan_id FROM subscription_plans WHERE platform = ? AND tier_name = ?",
                (PLATFORM_ASTROROSHNI, tier_name),
            )
            if cursor.fetchone() is None:
                plan_name_slug = tier_name.replace(" ", "_").lower()
                cursor.execute("""
                    INSERT INTO subscription_plans (platform, plan_name, price, duration_months, features, is_active, tier_name, discount_percent, google_play_product_id)
                    VALUES (?, ?, ?, 1, '{"tier": true}', 1, ?, ?, ?)
                """, (PLATFORM_ASTROROSHNI, plan_name_slug, price, tier_name, discount_percent, product_id))
                conn.commit()

        # 6) Backfill discount_percent for existing VIP plans that still have 0 (e.g. existed before tier columns)
        try:
            for tier_name, discount_percent, product_id, price in vip_plans:
                plan_name_slug = tier_name.replace(" ", "_").lower()
                cursor.execute(
                    """
                    UPDATE subscription_plans
                    SET discount_percent = ?, tier_name = ?, google_play_product_id = COALESCE(google_play_product_id, ?)
                    WHERE (tier_name = ? OR plan_name = ?) AND platform = ? AND (discount_percent IS NULL OR discount_percent = 0)
                    """,
                    (discount_percent, tier_name, product_id, tier_name, plan_name_slug, PLATFORM_ASTROROSHNI),
                )
            conn.commit()
        except sqlite3.OperationalError:
            pass  # discount_percent column may not exist on very old DBs; step 3 adds it

        # 7) Sync google_play_product_id to Play Console IDs (subscription_vip_silver, subscription_vip_gold, subscription_vip_platinum)
        try:
            for tier_name, _discount, product_id, _price in vip_plans:
                cursor.execute(
                    "UPDATE subscription_plans SET google_play_product_id = ? WHERE platform = ? AND tier_name = ?",
                    (product_id, PLATFORM_ASTROROSHNI, tier_name),
                )
            conn.commit()
        except sqlite3.OperationalError:
            pass
    finally:
        conn.close()


if __name__ == "__main__":
    ensure_subscription_tier_schema()
    print("Subscription tier schema and seed completed.")
