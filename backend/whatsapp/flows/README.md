# WhatsApp Flow JSON (source of truth in repo)

Edit **`birth_chart_flow.json`** here, then copy the contents into **WhatsApp Manager → Flows → your flow → JSON** and publish.

This file is **not** loaded by the Python app at runtime; Meta hosts the published Flow. Keeping JSON in git avoids losing work and makes reviews easier.

See **`../FLOWS.md`** for endpoint URL, env vars (`WHATSAPP_FLOW_*`), and backend behavior.
