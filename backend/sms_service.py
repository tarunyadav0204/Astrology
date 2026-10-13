import os
from typing import Optional

import requests
from twilio.rest import Client


class SMSService:
    def __init__(self):
        self.provider = (os.getenv("SMS_PROVIDER") or "auto").strip().lower()
        self.mtalkz_api_key = (os.getenv("MTALKZ_API_KEY") or "").strip()
        self.mtalkz_sender_id = (os.getenv("MTALKZ_SENDER_ID") or "").strip()
        self.mtalkz_template_id = (os.getenv("MTALKZ_TEMPLATE_ID") or "").strip()
        self.mtalkz_pe_id = (os.getenv("MTALKZ_PE_ID") or "").strip()
        self.mtalkz_message = (os.getenv("MTALKZ_OTP_MESSAGE") or "").strip()
        self.mtalkz_url = (os.getenv("MTALKZ_SMS_URL") or "https://msg.mtalkz.com/V2/http-api-post.php").strip()

        # Twilio fallback / non-India support
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.twilio_client = None

        # Existing providers retained as fallback.
        self.msg91_auth_key = (os.getenv("MSG91_AUTH_KEY") or "").strip()
        self.msg91_template_id = (os.getenv("MSG91_TEMPLATE_ID") or "").strip()
        self.msg91_flow_url = (
            os.getenv("MSG91_FLOW_URL") or "https://control.msg91.com/api/v5/flow/"
        ).strip()
        self.msg91_short_url = (os.getenv("MSG91_SHORT_URL") or "0").strip()
        self.msg91_otp_variable_key = (os.getenv("MSG91_OTP_VARIABLE_KEY") or "numeric").strip()

        print(f"SMS Service Init - Primary: MTalkz; fallback selection: {self.provider}")
        print(
            f"SMS Service Init - MTalkz configured: {bool(self.mtalkz_api_key and self.mtalkz_sender_id and self.mtalkz_template_id and '{otp}' in self.mtalkz_message)}"
        )
        print(
            f"SMS Service Init - MSG91 configured: {bool(self.msg91_auth_key and self.msg91_template_id)}"
        )
        print(
            f"SMS Service Init - Twilio configured: {bool(self.account_sid and self.auth_token and self.from_number)}"
        )

        if all([self.account_sid, self.auth_token, self.from_number]):
            try:
                self.twilio_client = Client(self.account_sid, self.auth_token)
                print("Twilio client initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Twilio client: {e}")
                self.twilio_client = None
        else:
            print("Twilio credentials incomplete. Twilio SMS fallback disabled.")

    def _normalize_india_mobile(self, phone_number: str) -> Optional[str]:
        raw = (
            (phone_number or "")
            .strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )
        digits = "".join(c for c in raw if c.isdigit())
        if raw.startswith('+'):
            return digits if raw.startswith('+91') and len(digits) == 12 else None
        if len(digits) == 12 and digits.startswith("91"):
            return digits
        if len(digits) == 10:
            return f"91{digits}"
        return None

    def _is_india_number(self, phone_number: str) -> bool:
        return self._normalize_india_mobile(phone_number) is not None

    def _send_via_msg91(self, phone_number: str, code: str) -> bool:
        if not self.msg91_auth_key or not self.msg91_template_id:
            print("MSG91 disabled - missing MSG91_AUTH_KEY or MSG91_TEMPLATE_ID")
            return False

        mobile = self._normalize_india_mobile(phone_number)
        if not mobile:
            print(f"MSG91 skipped - non-India or invalid number: {phone_number}")
            return False

        payload = {
            "template_id": self.msg91_template_id,
            "short_url": self.msg91_short_url,
            "recipients": [
                {
                    "mobiles": mobile,
                    self.msg91_otp_variable_key: str(code),
                }
            ],
        }
        headers = {
            "authkey": self.msg91_auth_key,
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                self.msg91_flow_url,
                json=payload,
                headers=headers,
                timeout=20,
            )
            content_type = (response.headers.get("content-type") or "").lower()
            response_text = (response.text or "")[:1000]

            if not (200 <= response.status_code < 300):
                print(
                    f"MSG91 send failed: status={response.status_code} content_type={content_type} body={response_text}"
                )
                return False

            try:
                data = response.json()
            except ValueError:
                print(
                    f"MSG91 unexpected non-JSON success response: status={response.status_code} content_type={content_type} body={response_text}"
                )
                return False

            status_value = str(data.get("type") or data.get("status") or "").strip().lower()
            has_request_marker = bool(
                data.get("request_id")
                or data.get("message")
                or data.get("data")
            )

            if status_value in {"success", "sent", "queued"} or (not status_value and has_request_marker):
                print(f"MSG91 accepted SMS request to {mobile}: {data}")
                return True

            print(
                f"MSG91 rejected/unknown response: status={response.status_code} body={data}"
            )
            return False
        except Exception as e:
            print(f"MSG91 send exception: {e}")
            return False

    def _send_via_twilio(self, phone_number: str, code: str) -> bool:
        if not self.twilio_client:
            print(f"Twilio disabled - would send code to {phone_number}")
            return False

        try:
            formatted = phone_number
            if not formatted.startswith("+"):
                if self._is_india_number(formatted):
                    india_mobile = self._normalize_india_mobile(formatted)
                    formatted = f"+{india_mobile}" if india_mobile else formatted
                else:
                    formatted = f"+91{formatted}"

            print(f"Attempting to send Twilio SMS to {formatted} from {self.from_number}")

            message = self.twilio_client.messages.create(
                body=f"Your AstroRoshni password reset code is: {code}. Valid for 10 minutes.",
                from_=self.from_number,
                to=formatted,
            )

            print(f"Twilio SMS sent successfully. SID: {message.sid}")
            return True
        except Exception as e:
            print(f"Failed to send Twilio SMS: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            return False

    def _send_via_mtalkz(self, phone_number: str, code: str) -> bool:
        mobile = self._normalize_india_mobile(phone_number)
        if not mobile:
            return False  # International numbers retain the existing Twilio path.
        if not (self.mtalkz_api_key and self.mtalkz_sender_id and self.mtalkz_template_id
                and self.mtalkz_message and '{otp}' in self.mtalkz_message):
            print('MTalkz OTP configuration incomplete; using fallback')
            return False
        payload = {
            'apikey': self.mtalkz_api_key,
            'senderid': self.mtalkz_sender_id,
            'number': mobile,
            'message': self.mtalkz_message.replace('{otp}', str(code)),
            'template_id': self.mtalkz_template_id,
            'format': 'json',
        }
        if self.mtalkz_pe_id:
            payload['pe_id'] = self.mtalkz_pe_id
        try:
            response = requests.post(self.mtalkz_url, json=payload, timeout=(3, 8))
            if not 200 <= response.status_code < 300:
                print(f'MTalkz SMS failed: HTTP {response.status_code}; using fallback')
                return False
            data = response.json()
            if not isinstance(data, dict) or str(data.get('status', '')).upper() != 'OK':
                print('MTalkz SMS request rejected; using fallback')
                return False
            recipients = data.get('data')
            accepted = (
                isinstance(recipients, list) and len(recipients) == 1
                and isinstance(recipients[0], dict)
                and str(recipients[0].get('mobile', '')).lstrip('+') == mobile
                and str(recipients[0].get('status', '')).upper() == 'SUBMITTED'
                and bool(recipients[0].get('id'))
            )
            if not accepted:
                print('MTalkz SMS submission not confirmed; using fallback')
            return bool(accepted)
        except Exception as error:
            # Provider exception text can contain the request body and API key.
            print(f'MTalkz SMS exception: {type(error).__name__}; using fallback')
            return False

    def send_reset_code(self, phone_number: str, code: str) -> bool:
        """Try MTalkz first, then the previously configured provider chain."""
        if self._send_via_mtalkz(phone_number, code):
            print('SMS OTP request accepted - provider=mtalkz')
            return True
        provider = self.provider
        print(f'SMS OTP using fallback - selection={provider}')

        def send_fallback(name, send):
            accepted = send(phone_number, code)
            if accepted:
                print(f'SMS OTP request accepted - provider={name}')
            return accepted

        if provider == "msg91":
            return send_fallback('msg91', self._send_via_msg91)
        if provider == "twilio":
            return send_fallback('twilio', self._send_via_twilio)

        # auto mode: use MSG91 for India, otherwise Twilio fallback
        if self._is_india_number(phone_number):
            if send_fallback('msg91', self._send_via_msg91):
                return True
            return send_fallback('twilio', self._send_via_twilio)

        if send_fallback('twilio', self._send_via_twilio):
            return True
        return send_fallback('msg91', self._send_via_msg91)


sms_service = SMSService()
