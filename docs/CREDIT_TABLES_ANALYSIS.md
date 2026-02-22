# Credit Tables Analysis

## Overview

Yes — from the credit tables you can see **who** (user), **how much** (amount), and **for what activity** (feature/usage). The main source of truth for usage is **`credit_transactions`**.

---

## Tables

### 1. `user_credits`

| Column       | Type      | Description                    |
|-------------|-----------|--------------------------------|
| id          | INTEGER   | Primary key                    |
| userid      | INTEGER   | User (FK → users.userid)       |
| credits     | INTEGER   | Current balance                |
| created_at  | TIMESTAMP |                                |
| updated_at  | TIMESTAMP |                                |

- **One row per user.** Answers: *current balance per user.*

---

### 2. `credit_transactions` (main ledger)

| Column           | Type      | Description |
|------------------|-----------|-------------|
| id               | INTEGER   | Primary key |
| userid           | INTEGER   | Who (FK → users) |
| transaction_type | TEXT      | `'earned'` \| `'spent'` \| `'refund'` |
| amount           | INTEGER   | + for earned/refund, **negative for spent** |
| balance_after    | INTEGER   | Balance after this transaction |
| source           | TEXT      | **Earned:** `'promo_code'`, `'admin_adjustment'`, `'credit_request_approval'`, etc. **Spent:** always `'feature_usage'` |
| reference_id     | TEXT      | **Activity identifier:** feature name for spends; promo code for some earns; etc. |
| description      | TEXT      | Optional human-readable text (e.g. "Standard Chat: How does...") |
| metadata         | TEXT      | Optional (currently unused in code) |
| created_at       | TIMESTAMP | When the transaction happened |

- **Who:** `userid`
- **How much:** `amount` (negative = spent)
- **What activity:** `reference_id` for spends; `source` + `reference_id` for earns

---

### 3. Other credit-related tables

- **`credit_settings`** — Cost per feature (e.g. `chat_question_cost` = 1, `karma_analysis_cost` = 25).
- **`promo_codes`** — Promo code definitions.
- **`promo_code_usage`** — Which user used which promo and how many credits they got.
- **`credit_requests`** — User requests for credits and admin approval (separate from the main ledger).

---

## How “what activity” is stored

When credits are **spent**, the code does:

```python
# credit_service.spend_credits(userid, amount, feature, description)
INSERT INTO credit_transactions (..., source, reference_id, description)
VALUES (..., 'feature_usage', feature, description)
```

So for **spends**:

- **`source`** = `'feature_usage'` (same for all feature usage).
- **`reference_id`** = **feature name** (this is the “activity”).
- **`description`** = optional detail (e.g. truncated question or “Wealth analysis for 1990-01-01”).

---

## Feature names used in code (`reference_id` for spends)

| reference_id (feature)   | Meaning / feature              |
|--------------------------|--------------------------------|
| `chat_question`          | Standard or premium chat       |
| `event_timeline`         | Cosmic Timeline / yearly events|
| `wealth_analysis`        | Wealth analysis                |
| `marriage_analysis`      | Marriage analysis              |
| `health_analysis`        | Health analysis                |
| `education_analysis`     | Education analysis             |
| `career_analysis`        | Career analysis                |
| `progeny_analysis`       | Progeny / childbirth analysis |
| `trading_daily`          | Daily trading forecast         |
| `trading_calendar`       | Monthly trading calendar       |
| `childbirth_planner`     | Childbirth muhurat              |
| `vehicle_purchase`       | Vehicle purchase muhurat       |
| `griha_pravesh`          | Griha pravesh muhurat          |
| `gold_purchase`          | Gold purchase muhurat          |
| `business_opening`       | Business opening muhurat       |
| `partnership_analysis`   | Partnership compatibility      |
| `karma_analysis`         | Karma analysis                 |
| `mundane_chat`           | Mundane (non-personal) chat    |

(Earned credits use **`source`** like `'promo_code'`, `'admin_adjustment'`, `'credit_request_approval'`, and often **`reference_id`** e.g. promo code string.)

---

## Example queries

### Who used how much for what (spends only)

```sql
SELECT
  ct.userid,
  u.name,
  u.phone,
  ct.reference_id AS activity,
  ct.amount,
  ct.balance_after,
  ct.description,
  ct.created_at
FROM credit_transactions ct
JOIN users u ON u.userid = ct.userid
WHERE ct.transaction_type = 'spent'
ORDER BY ct.created_at DESC;
```

### Usage summary by activity

```sql
SELECT
  reference_id AS activity,
  COUNT(*) AS transaction_count,
  SUM(-amount) AS total_credits_spent
FROM credit_transactions
WHERE transaction_type = 'spent'
  AND source = 'feature_usage'
GROUP BY reference_id
ORDER BY total_credits_spent DESC;
```

### Usage by user (totals per user)

```sql
SELECT
  ct.userid,
  u.name,
  u.phone,
  SUM(-ct.amount) AS total_spent,
  COUNT(*) AS transaction_count
FROM credit_transactions ct
JOIN users u ON u.userid = ct.userid
WHERE ct.transaction_type = 'spent'
GROUP BY ct.userid
ORDER BY total_spent DESC;
```

### Credits earned by source (promo, admin, etc.)

```sql
SELECT
  source,
  reference_id,
  COUNT(*) AS count,
  SUM(amount) AS total_credits
FROM credit_transactions
WHERE transaction_type IN ('earned', 'refund')
GROUP BY source, reference_id;
```

---

## Gap: `reference_id` not in history API

- **`get_transaction_history()`** in `credit_service.py` returns: `transaction_type`, `amount`, `balance_after`, `source`, `description`, `created_at` — it does **not** return **`reference_id`**.
- So the **activity** (feature name) is in the DB but not exposed in the user or admin history API. The admin ledger UI has a `getFeatureName(source, referenceId)` but never receives `referenceId`.

**Recommendation:** Include `reference_id` in the transaction history response (and in the admin user-history endpoint) so “what activity” is visible in the app and in any reports built on that API.
