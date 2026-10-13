# SMS OTP providers

All login/registration, password-reset and WhatsApp registration SMS OTPs use
`SMSService.send_reset_code`. For Indian numbers the order is MTalkz, followed by
the existing provider selection. With `SMS_PROVIDER=auto` (the default), fallback
is MSG91 then Twilio. Existing `msg91` and `twilio` selections choose the fallback
provider; they do not bypass MTalkz. International numbers retain the existing
Twilio path because the supplied MTalkz international API is a separate endpoint.

Set these backend environment variables, then restart the backend:

```dotenv
MTALKZ_API_KEY=<secret API key>
MTALKZ_SENDER_ID=<approved six-character sender ID>
MTALKZ_TEMPLATE_ID=<approved DLT OTP template ID>
MTALKZ_OTP_MESSAGE="<exact approved message text with {otp} in place of the code>"
MTALKZ_PE_ID=<principal entity ID, if required for your account>
MTALKZ_SMS_URL=https://msg.mtalkz.com/V2/http-api-post.php
```

The message text must match the approved template, including punctuation. A
missing configuration skips MTalkz and retains existing SMS availability. The
API key belongs in the deployment secret store/environment, never source control.

MTalkz requests use JSON POST and a bounded 3-second connection/8-second read
timeout. Only an HTTP success with `status=OK` and a matching recipient carrying
`status=SUBMITTED` and a message ID stops fallback. Rejections, malformed replies,
HTTP failures and exceptions fall back using the same OTP code. Submission is
provider acceptance, not handset delivery confirmation. Delivery-report-based
retry is not implemented; a timeout after provider acceptance can cause duplicate
SMS messages, both containing the same valid code.

Run mocked provider tests (no paid SMS is sent):

```sh
backend/.venv/bin/python -m pytest backend/tests/test_sms_mtalkz.py -q
```
