"""
Decrypt / encrypt WhatsApp Flow data endpoint payloads (data_api_version 3.0).

See: https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint/
"""
from __future__ import annotations

import json
import logging
from base64 import b64decode, b64encode
from typing import Any, Dict, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.padding import MGF1, OAEP
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import load_pem_private_key

logger = logging.getLogger(__name__)


def _normalize_pem(pem: str) -> str:
    pem = (pem or "").strip()
    # Strip UTF-8 BOM (common when copying from Windows / some editors).
    if pem.startswith("\ufeff"):
        pem = pem.lstrip("\ufeff").strip()
    pem = pem.replace("\r\n", "\n").replace("\r", "\n")
    # Env / Docker often stores PEM as one line with literal \n (or double-escaped \\n).
    for _ in range(8):
        if "\\n" not in pem:
            break
        pem = pem.replace("\\n", "\n")
    return pem.strip()


def decrypt_flow_request(
    encrypted_flow_data_b64: str,
    encrypted_aes_key_b64: str,
    initial_vector_b64: str,
    private_key_pem: str,
) -> Tuple[Dict[str, Any], bytes, bytes]:
    """
    Returns (decrypted_json_dict, aes_key_bytes, iv_bytes).
    """
    pem = _normalize_pem(private_key_pem)
    try:
        private_key = load_pem_private_key(pem.encode("utf-8"), password=None)
    except ValueError as e:
        logger.error(
            "flow_crypto: could not load Flow RSA private key PEM (%s). "
            "Fix: use WHATSAPP_FLOW_PRIVATE_KEY_FILE pointing to a PEM file (chmod 600), "
            "or put a multi-line RSA key in .env with \\n between lines. "
            "Must be RSA (not EC), match the public key on Graph for this phone_number_id.",
            e,
        )
        raise

    flow_data = b64decode(encrypted_flow_data_b64)
    iv = b64decode(initial_vector_b64)
    encrypted_aes_key = b64decode(encrypted_aes_key_b64)

    aes_key = private_key.decrypt(
        encrypted_aes_key,
        OAEP(mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )

    encrypted_flow_data_body = flow_data[:-16]
    encrypted_flow_data_tag = flow_data[-16:]
    decryptor = Cipher(algorithms.AES(aes_key), modes.GCM(iv, encrypted_flow_data_tag)).decryptor()
    decrypted_data_bytes = decryptor.update(encrypted_flow_data_body) + decryptor.finalize()
    decrypted_data = json.loads(decrypted_data_bytes.decode("utf-8"))
    if not isinstance(decrypted_data, dict):
        raise ValueError("decrypted flow payload is not a JSON object")
    return decrypted_data, aes_key, iv


def encrypt_flow_response(response: Dict[str, Any], aes_key: bytes, iv: bytes) -> str:
    """Encrypt JSON response; return base64 string (Meta: Content-Type text/plain)."""
    flipped_iv = bytes(b ^ 0xFF for b in iv)
    encryptor = Cipher(algorithms.AES(aes_key), modes.GCM(flipped_iv)).encryptor()
    payload = json.dumps(response, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ciphertext = encryptor.update(payload) + encryptor.finalize()
    tag = encryptor.tag
    return b64encode(ciphertext + tag).decode("utf-8")
