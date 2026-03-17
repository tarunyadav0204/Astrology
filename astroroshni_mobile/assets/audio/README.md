# Cosmic ambience (podcast player)

You **do not need to add any MP3 file** to this folder for the Cosmic ambience feature.

## How to enable it

Set **`COSMIC_AMBIENT_URL`** in **`src/utils/constants.js`** to the **direct URL** of an MP3 file.

- **Where to set it:** `astroroshni_mobile/src/utils/constants.js`  
  Find the line:  
  `export const COSMIC_AMBIENT_URL = '';`  
  and set it to your URL, for example:  
  `export const COSMIC_AMBIENT_URL = 'https://your-server.com/ambient-loop.mp3';`

- **What kind of MP3:** A **30–60 second ambient loop** (soft pad, space drone, meditation tone, etc.) that can be looped seamlessly. The app will play it at low volume behind the podcast.

- **Where to get/host the MP3:**
  - Host your own file (e.g. on your backend or a CDN) and use that URL.
  - Or use a free track from [Pixabay](https://pixabay.com/sound-effects/search/ambient/), [Freesound](https://freesound.org/) (check license), or similar; you’ll need a **direct link** to the MP3 (not just the page URL).

Leave `COSMIC_AMBIENT_URL` as `''` if you don’t want the Cosmic ambience toggle to appear.
