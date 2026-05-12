import os
from typing import Optional

import requests
from twilio.rest import Client


class SMSService:
    def __init__(self):
        self.provider = (os.getenv("SMS_PROVIDER") or "auto").strip().lower()

        # Twilio fallback / non-India support
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.twilio_client = None

        # MSG91 primary path for India OTP
        self.msg91_auth_key = (os.getenv("MSG91_AUTH_KEY") or "").strip()
        self.msg91_template_id = (os.getenv("MSG91_TEMPLATE_ID") or "").strip()
        self.msg91_flow_url = (
            os.getenv("MSG91_FLOW_URL") or "https://control.msg91.com/api/v5/flow/"
        ).strip()
        self.msg91_short_url = (os.getenv("MSG91_SHORT_URL") or "0").strip()
        self.msg91_otp_variable_key = (os.getenv("MSG91_OTP_VARIABLE_KEY") or "numeric").strip()

        print(f"SMS Service Init - Provider: {self.provider}")
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
        if raw.startswith("+91") and len(digits) >= 12:
            return digits[-12:]
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

            if status_value in {"success", "sent", "queued"} or has_request_marker:
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

    def send_reset_code(self, phone_number: str, code: str) -> bool:
        """Send OTP via configured provider, preferring MSG91 for India when available."""
        provider = self.provider

        if provider == "msg91":
            return self._send_via_msg91(phone_number, code)
        if provider == "twilio":
            return self._send_via_twilio(phone_number, code)

        # auto mode: use MSG91 for India, otherwise Twilio fallback
        if self._is_india_number(phone_number):
            if self._send_via_msg91(phone_number, code):
                return True
            return self._send_via_twilio(phone_number, code)

        if self._send_via_twilio(phone_number, code):
            return True
        return self._send_via_msg91(phone_number, code)


sms_service = SMSService()
