# Support image attachments

Users of `astroroshni_mobile` (native and PWA) can select one optional JPEG/PNG
when creating a ticket or replying. A text message is still required. Existing
text-only clients and admin PDF replies remain compatible. The admin inbox uses
the existing authenticated attachment download action for both images and PDFs.

## Server boundary

- Optional `image_base64` field on the existing JSON create/reply endpoints.
  Raw request streams are capped before JSON parsing, including chunked bodies.
- Authentication is required. Replies check ticket ownership and closed status
  before decoding or saving images.
- 5 MiB input/output, 12 million pixels, maximum side 8192 pixels, single frame.
  Only Pillow's JPEG and PNG decoders are selected. Client filenames and MIME
  declarations are not used to establish file type.
- Uploaded files are decoded and converted to a fresh pixel-only JPEG. Original
  bytes, EXIF/GPS, comments, profiles, filenames, and appended data are discarded.
- Two concurrent image decodes per worker; busy requests receive HTTP 429.
- Existing ticket/message limits still apply. Image uploads additionally allow
  20 per user per rolling 24 hours and 50 MiB stored per user. PostgreSQL advisory
  transaction locks serialize quota checks and inserts for the same user.
- Random server filenames and private file permissions. Failed database writes
  roll back and remove newly written files.
- Downloads require the owner or admin. Resolved paths must be in the attachment
  directory. Responses use attachment disposition, `nosniff`, `private, no-store`,
  and a restrictive CSP. Do not expose this directory via static hosting.

## Release and operations

Deploy backend first, then PWA/admin assets. Install the updated Pillow requirement
(12.3.0 requires Python 3.10+). Native clients need a new binary containing
`expo-document-picker`; a JavaScript-only update is insufficient for that dependency.

The JSON representation is about one third larger than the input image. A reverse
proxy must allow at least 7 MiB for these two support POST routes; keep a bounded
body-size limit and authenticated API rate limiting at the edge. Monitor disk
usage and maintain private persistent storage/backups. The 50 MiB account cap
does not replace an operational global disk quota or retention policy.

This is layered risk reduction, not a guarantee that uploads cannot be exploited.
Keep the decoder and API dependencies patched. Admin PDFs retain their existing
validation path; this change does not add malware scanning to PDFs.

Validation: `python -m pytest backend/test_support_images.py -q` exercises actual
routes with a disposable database adapter and no external accounts or mail.
PostgreSQL locking itself and native device picking should be checked in staging.

Reference: [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
