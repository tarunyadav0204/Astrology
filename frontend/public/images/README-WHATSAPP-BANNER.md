# Homepage images (`public/images`)

## WhatsApp homepage banner (9:16)

Add your portrait promo here:

**File name:** `whatsapp-home-banner.png`  
**Recommended size:** **1080 × 1920** px (or any **9:16** ratio, e.g. 720×1280).  
**Path on disk:** `frontend/public/images/whatsapp-home-banner.png`  
**URL in the app:** `/images/whatsapp-home-banner.png`

After the user closes the popup once, it stays hidden until they clear site data (key: `ar_home_whatsapp_banner_dismissed_v1` in `localStorage`).

### Optional: tap opens WhatsApp

In the frontend `.env` (or your deployment env), set:

`REACT_APP_WHATSAPP_CHAT_URL=https://wa.me/<your_number_without_plus>`

Example: `REACT_APP_WHATSAPP_CHAT_URL=https://wa.me/919876543210`
