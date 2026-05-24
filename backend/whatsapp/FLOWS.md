# WhatsApp Flows (Meta) — setup + this repo

WhatsApp **Flows** are multi-screen forms inside WhatsApp. They are **separate** from interactive **list** messages (chart picker).

## What you configure in Meta (portal)

1. **WhatsApp Manager** (linked to your WABA) → **Flows** (or use Meta’s [Flow playground](https://developers.facebook.com/docs/whatsapp/flows/playground) while iterating).
2. **Design** screens in the Flow builder (Flow JSON), set the **complete** action so submitted fields appear in the webhook `response_json` (see Meta’s Flow JSON reference).
3. **Publish** the Flow and copy **`flow_id`** (numeric string from Manager). Alternatively Cloud API can reference **`flow_name`** if you use that instead.
4. **Prerequisites** (Meta): [Business verification](https://developers.facebook.com/docs/development/release/business-verification) and good **message quality** may be required for some Flow usage — see [Sending a Flow](https://developers.facebook.com/docs/whatsapp/flows/guides/sendingaflow/).
5. **Webhooks** (Developer App → **WhatsApp** → **Configuration** → Webhooks → **Manage**):  
   - Stay subscribed to **`messages`** (you already receive `nfm_reply` here when a user submits a Flow).  
   - Also subscribe to **`flows`** if you want Flow *status / health* events (optional for basic submit handling).  
   Same **Callback URL** as `/api/webhooks/whatsapp` is fine if your app routes those payloads (today we only act on `messages`).

## What you configure in AstroRoshni (env)

Set **either** `WHATSAPP_BIRTHCHART_FLOW_ID` **or** `WHATSAPP_BIRTHCHART_FLOW_NAME` (from Meta). When set, **“Add new chart”** (`NEW` / list row `cr_new`) opens the Flow instead of only sending the website link.

| Variable | Purpose |
|----------|---------|
| `WHATSAPP_BIRTHCHART_FLOW_ID` | Published Flow ID from WhatsApp Manager |
| `WHATSAPP_BIRTHCHART_FLOW_NAME` | Alternative to ID (Cloud API) |
| `WHATSAPP_BIRTHCHART_FLOW_CTA` | Button label (≤ ~30 chars, no emoji per Meta) |
| `WHATSAPP_BIRTHCHART_FLOW_MODE` | `published` (default) or `draft` while testing edits |
| `WHATSAPP_BIRTHCHART_FLOW_HEADER` | Optional short header text |
| `WHATSAPP_BIRTHCHART_FLOW_BODY` | Intro body above the CTA |
| `WHATSAPP_BIRTHCHART_FLOW_FOOTER` | Optional footer |
| `WHATSAPP_BIRTHCHART_FLOW_SCREEN` | Optional first screen id (not `FIRST_ENTRY_SCREEN`) |

`WHATSAPP_ACCESS_TOKEN` must allow sending **interactive** `type: flow` messages.

For WhatsApp registration, set **either** `WHATSAPP_REGISTRATION_FLOW_ID` **or** `WHATSAPP_REGISTRATION_FLOW_NAME`. When set, a new WhatsApp number that does not match an existing user opens the registration Flow instead of the older text-by-text signup.

| Variable | Purpose |
|----------|---------|
| `WHATSAPP_REGISTRATION_FLOW_ID` | Published registration Flow ID from WhatsApp Manager |
| `WHATSAPP_REGISTRATION_FLOW_NAME` | Alternative to ID (Cloud API) |
| `WHATSAPP_REGISTRATION_FLOW_CTA` | Button label, default `Create account` |
| `WHATSAPP_REGISTRATION_FLOW_MODE` | `published` (default) or `draft` while testing |
| `WHATSAPP_REGISTRATION_FLOW_HEADER` | Optional short header, default `AstroRoshni` |
| `WHATSAPP_REGISTRATION_FLOW_BODY` | Intro body above the CTA |
| `WHATSAPP_REGISTRATION_FLOW_FOOTER` | Optional footer |
| `WHATSAPP_REGISTRATION_FLOW_SCREEN` | First screen id, default `registration_welcome` |

## How the backend behaves

- **First contact (softer onboarding):** the first **non-empty text** while `whatsapp_sessions.state` is `idle` and `idle_soft_intro_done` is false sends a short **nudge**, then runs the same **phone / account lookup** as “hi” (`_handle_idle_greeting`—chart list, link, or SMS OTP). The flag `idle_soft_intro_done` is then set so later idle messages are not auto-routed again (unless the user sends a greeting again, which still re-runs the greeting handler).
- **Chart chat (Standard):** when a user has an **`active_chart_id`** and sends a normal text question (not a greeting / menu keyword), the server replies with a short wait line, then runs the same **`POST /api/chat-v2/ask`** pipeline as the mobile app (`chat_tier: standard`, `premium_analysis: false`). Replies are polled via **`GET /api/chat-v2/status/{message_id}`** and sent on WhatsApp in **≤4090-character chunks**. After the reading, a short line summarizes **credits charged** (from balance before vs after) and **current balance**. The worker calls your own HTTP API, so set **`WHATSAPP_INTERNAL_API_URL`** (or **`ASTRO_INTERNAL_API_URL`** / **`PUBLIC_API_BASE_URL`**) to the backend base URL the worker can reach (same host and **port** the process listens on, e.g. `http://127.0.0.1:8001`). If unset, the default is `http://127.0.0.1:$PORT` using **`PORT`** or **`UVICORN_PORT`**, then **8001** (matches `main.py` when `PORT` is not set). A wrong port causes *connection refused* on `/api/chat-v2/ask`.
- On **Flow open**, we generate a **`flow_token`**, store it in `whatsapp_sessions.pending_flow_token`, and set state **`await_flow_birth`**.
- On submit, Meta sends an **`interactive` / `nfm_reply`** message; `response_json` is a **string** containing JSON that **includes the same `flow_token`** plus your form fields. We verify the token, log field **names**, clear the token, and reply with a confirmation.  
- **Persisting** answers into `birth_charts`: `_handle_flow_completion` in `handlers.py` maps the Flow `complete` payload to `BirthData` and calls `persist_birth_chart_for_user` in `charts/routes.py` (same insert/dedupe/encryption path as `POST /charts/calculate-chart`). Timezone is **not** taken from the client; it is derived from latitude/longitude on the server.

## Flow data endpoint (Google place search inside the Flow)

Manager **Endpoint URL** (example): `https://astroroshni.com/api/webhooks/whatsapp-flow`

This route is **separate** from `/api/webhooks/whatsapp` (messages). Meta sends **encrypted** JSON (`encrypted_flow_data`, `encrypted_aes_key`, `initial_vector`); the server decrypts, runs logic, returns **base64 encrypted** JSON as **`text/plain`** (see Meta’s [Implementing endpoint for Flows](https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint/)).

### Env

| Variable | Purpose |
|----------|---------|
| `WHATSAPP_FLOW_PRIVATE_KEY` | PEM of the **RSA private key** that pairs with the **public key** you registered via Graph `POST .../whatsapp_business_encryption`. Use real newlines in a file-based secret, or `\n` in a single-line env value. |
| `WHATSAPP_APP_SECRET` | Same as message webhooks — used to verify **`X-Hub-Signature-256`** on this endpoint (recommended in production). |
| `GOOGLE_PLACES_API_KEY` | Required for place **autocomplete** / **details** inside `flow_data_handler`. |

Optional overrides (defaults match a typical birth-chart Flow layout):

| Variable | Default |
|----------|---------|
| `WHATSAPP_FLOW_DATA_INIT_SCREEN` | `create_birth_chart` |
| `WHATSAPP_FLOW_DATA_SCREEN_SEARCH` | `place_search` |
| `WHATSAPP_FLOW_DATA_SCREEN_PICK` | `place_pick` |
| `WHATSAPP_FLOW_DATA_SCREEN_AFTER_PLACE` | `birth_place_gender` |
| `WHATSAPP_FLOW_DATA_FIELD_PLACE_QUERY` | `place_query` |
| `WHATSAPP_FLOW_DATA_FIELD_SELECTED_PLACE` | `selected_place` |

### Flow JSON expectations (for autocomplete)

1. Screen **`place_search`** (id configurable): `TextInput` **`name` = `place_query`**, Footer **`data_exchange`** (payload includes `place_query`).  
2. Screen **`place_pick`**: **`RadioButtonsGroup`** (options show on the same screen; a **`Dropdown`** needs an extra tap to open the list) with **`data-source`: `${data.place_options}`** (array of `{ "id", "title" }` from the server). Each **`title`** must be **≤ 30 characters** (Meta rule); the server truncates Google descriptions automatically. **`name` = `selected_place`**. Footer **`data_exchange`** to resolve coordinates.  
3. Server returns **`data`** with `selected_latitude`, `selected_longitude`, `selected_formatted_address`, `selected_place_id` on the next screen — bind these in your Flow JSON as needed.

Until those screens exist in your published Flow, the endpoint still answers Meta **`ping`** (health check) and **`init`** (first screen; Meta may send `init` or `INIT` — the server normalizes to lowercase).

**Birth chart Flow JSON in repo:** edit `whatsapp/flows/birth_chart_flow.json`, then paste into WhatsApp Manager (the app does not load this file at runtime). Birth time is collected as **`birth_hour`** + **`birth_minute`** (dropdowns `00`–`23` and `00`–`59`); your webhook should join them as `HH:MM` for storage.

### Meta error `139000` — “Blocked by Integrity”

If Graph returns **`(#139000) Blocked by Integrity`** / **`Integrity requirements not met`** when **sending** a Flow, that is a **Meta / WABA restriction**, not an application bug. See Meta’s [Flow error codes](https://developers.facebook.com/docs/whatsapp/flows/reference/error-codes/). Check Business Suite for account or quality issues, ensure Flow JSON includes required **`version`** / **`data_api_version`**, and use [Meta business direct support](https://business.facebook.com/direct-support) if the block persists.

### Health check returns HTTP 421 (empty body)

That status is returned when **decrypt** or **encrypt** throws (see server logs).

| Cause | What to do |
|--------|------------|
| **Private key ≠ public key** uploaded to `.../whatsapp_business_encryption` for this **Phone number ID** | Regenerate a pair, re-`POST` the **public** key, put the matching **private** key on the server. Verify with Graph `GET .../whatsapp_business_encryption` → `business_public_key_signature_status` should be **`VALID`**. |
| **PEM mangled in `.env`** | Use **`WHATSAPP_FLOW_PRIVATE_KEY_FILE`** pointing to a `chmod 600` PEM file on the host instead of a giant env var. Avoid wrapping the PEM in extra quotes unless your loader strips them (we strip one layer of `"` / `'`). |
| **Wrong phone number** | The health check uses the number shown in Manager; the public key must be registered for that number’s **`PHONE_NUMBER_ID`**. |

OpenSSL check (modulus of public vs private must match):

```bash
# Works on common OpenSSL / macOS LibreSSL (avoid `pkey -modulus` — not everywhere).
openssl rsa -noout -modulus -in flow_endpoint_private.pem | openssl md5
openssl rsa -pubin -noout -modulus -in flow_endpoint_public.pem | openssl md5
```

## References

- [Sending a Flow](https://developers.facebook.com/docs/whatsapp/flows/guides/sendingaflow/) (templates vs interactive CTA).
- [Receive Flow response](https://developers.facebook.com/docs/whatsapp/flows/guides/receiveflowresponse/) (`nfm_reply` / `response_json`).
- [Flow JSON](https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/).
- [Implementing endpoint for Flows](https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint/) (encrypt/decrypt, `ping`, `data_exchange`).
