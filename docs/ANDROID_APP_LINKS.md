# Android App Links

AstroRoshni uses Android App Links to connect public web URLs on `astroroshni.com`
to screens inside the Android app.

## Implemented URLs

- `https://astroroshni.com/karma-analysis` -> `KarmaAnalysis`
- `https://astroroshni.com/kundli-matching` -> `RelationshipMatch`
- `https://astroroshni.com/marriage-analysis` -> `RelationshipMatch`
- `https://astroroshni.com/blog` -> `BlogList`
- `https://astroroshni.com/blog/:slug` -> `BlogPostDetail`
- `https://astroroshni.com/panchang` -> `UniversalMuhurat`
- `https://astroroshni.com/muhurat-finder` -> `MuhuratHub`
- `https://astroroshni.com/nakshatras` -> `NakshatraCalendar`

The same paths are configured for `www.astroroshni.com`.

## Website Verification

The Digital Asset Links file is:

```text
frontend/public/.well-known/assetlinks.json
```

After deployment it must be reachable at:

```text
https://astroroshni.com/.well-known/assetlinks.json
https://www.astroroshni.com/.well-known/assetlinks.json
```

It currently contains the SHA-256 fingerprint from the checked-in Android upload
keystore:

```text
E9:99:50:35:93:C8:88:CC:11:BD:17:D4:41:BE:86:2A:41:C3:C1:D9:D7:60:DA:23:F4:25:E2:4E:A6:FD:51:58
```

If Google Play App Signing is enabled, also add the **App signing key
certificate** SHA-256 fingerprint from Play Console:

```text
Play Console -> Setup -> App integrity -> App signing key certificate
```

Keep both fingerprints in `sha256_cert_fingerprints` if the upload certificate
and Play signing certificate differ.

## Local Verification

After installing a release build on a device:

```bash
adb shell pm get-app-links com.astroroshni.mobile
adb shell am start -W -a android.intent.action.VIEW -d "https://astroroshni.com/karma-analysis" com.astroroshni.mobile
```

If verification is pending or failed, check that the deployed `assetlinks.json`
returns HTTP 200 with `Content-Type: application/json` or another non-HTML JSON
compatible content type.
