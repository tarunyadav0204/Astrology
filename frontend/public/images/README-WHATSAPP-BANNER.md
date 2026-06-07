# Homepage WhatsApp banner (9:16)

The app **does not** load `whatsapp-home-banner.png` by default (it was several MB and hurt LCP).

## What the site uses

| Role | File |
|------|------|
| **WebP (preferred)** | `whatsapp-home-banner-480.webp`, `whatsapp-home-banner-720.webp` (responsive `srcset`) |
| **Fallback (JPEG)** | `whatsapp-home-banner-720.jpg` |

Paths are set in `src/config/app.config.js` under `whatsappHomeBanner`.

## Updating the artwork

1. Export a **9:16** portrait (e.g. **720×1280** or **1080×1920**).
2. Replace or add a **working source** file (e.g. save as `whatsapp-home-banner.png` in this folder only if you use it as input).
3. Regenerate derivatives on macOS (from `frontend/public/images/`):

```bash
sips -z 1280 720 whatsapp-home-banner.png --out _tmp-720.png
sips -z 854 480 whatsapp-home-banner.png --out _tmp-480.png
cwebp -q 84 _tmp-720.png -o whatsapp-home-banner-720.webp
cwebp -q 82 _tmp-480.png -o whatsapp-home-banner-480.webp
sips -s format jpeg -s formatOptions 78 _tmp-720.png --out whatsapp-home-banner-720.jpg
rm -f _tmp-720.png _tmp-480.png
```

(Requires [WebP](https://developers.google.com/speed/webp/download) `cwebp` on your PATH.)

After the user closes the popup once, it stays hidden until they clear site data (`localStorage` key: `ar_home_whatsapp_banner_dismissed_v1`).

### Optional: tap opens WhatsApp

In the frontend `.env` (or deployment env), set:

`REACT_APP_WHATSAPP_CHAT_URL=https://wa.me/<your_number_without_plus>`

Example: `REACT_APP_WHATSAPP_CHAT_URL=https://wa.me/919876543210`
