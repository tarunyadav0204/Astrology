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

## How the backend behaves

- On **Flow open**, we generate a **`flow_token`**, store it in `whatsapp_sessions.pending_flow_token`, and set state **`await_flow_birth`**.
- On submit, Meta sends an **`interactive` / `nfm_reply`** message; `response_json` is a **string** containing JSON that **includes the same `flow_token`** plus your form fields. We verify the token, log field **names**, clear the token, and reply with a confirmation.  
- **Persisting** answers into `birth_charts` is **not** implemented yet — field names depend on your Flow JSON; extend `_handle_flow_completion` in `handlers.py` when your form is fixed.

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
2. Screen **`place_pick`**: `Dropdown` with **`data-source`: `${data.place_options}`** (array of `{ "id", "title" }` from the server). **`name` = `selected_place`**. Footer **`data_exchange`** to resolve coordinates.  
3. Server returns **`data`** with `selected_latitude`, `selected_longitude`, `selected_formatted_address`, `selected_place_id` on the next screen — bind these in your Flow JSON as needed.

Until those screens exist in your published Flow, the endpoint still answers Meta **`ping`** (health check) and **`INIT`**.

## References

- [Sending a Flow](https://developers.facebook.com/docs/whatsapp/flows/guides/sendingaflow/) (templates vs interactive CTA).
- [Receive Flow response](https://developers.facebook.com/docs/whatsapp/flows/guides/receiveflowresponse/) (`nfm_reply` / `response_json`).
- [Flow JSON](https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/).
- [Implementing endpoint for Flows](https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint/) (encrypt/decrypt, `ping`, `data_exchange`).
