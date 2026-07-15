"""
ZEGOCLOUD Token04 generator.

Port of ZEGOCLOUD's official server assistant (token04) for Python.
Generates the HMAC-based token that the Flutter Live Audio Room Kit passes
to the ZEGO server for room-login privilege validation.

Reference: https://github.com/ZEGOCLOUD/zego_server_assistant (token/python/token04)

SECURITY: ServerSecret must NEVER ship in the client. This runs server-side only.
The client requests a token from /api/rtc/token and receives a short-lived,
room-scoped string.
"""

import base64
import json
import os
import struct
import time

from Crypto.Cipher import AES  # pip install pycryptodome


class TokenError(Exception):
    pass


# --- privilege keys (for user privilege tokens) ---
PRIVILEGE_LOGIN = 1   # room login
PRIVILEGE_PUBLISH = 2  # stream publish


def _make_nonce() -> int:
    # 31-bit random, matching the reference implementation's range
    return int.from_bytes(os.urandom(4), "big") & 0x7FFFFFFF


def _aes_pkcs5_pad(data: bytes, block_size: int = 16) -> bytes:
    pad = block_size - (len(data) % block_size)
    return data + bytes([pad] * pad)


def _aes_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(_aes_pkcs5_pad(plaintext))


def generate_token04(
    app_id: int,
    user_id: str,
    server_secret: str,
    effective_time_seconds: int = 3600,
    payload: str = "",
) -> str:
    """
    Generate a ZEGOCLOUD Token04.

    app_id:                  numeric ZEGO AppID
    user_id:                 stable per-user ID (we use the Django user id)
    server_secret:           32-char ZEGO ServerSecret (server-side only)
    effective_time_seconds:  token lifetime; we use short windows (1-2h)
    payload:                 "" for a user-identity token, or a JSON string
                             for a user-privilege token (room/stream scoped)
    """
    if not isinstance(app_id, int):
        raise TokenError("app_id must be an int")
    if not user_id or not isinstance(user_id, str):
        raise TokenError("user_id must be a non-empty string")
    if len(server_secret) != 32:
        raise TokenError("server_secret must be exactly 32 bytes")
    if effective_time_seconds <= 0:
        raise TokenError("effective_time_seconds must be > 0")

    create_time = int(time.time())
    nonce = _make_nonce()
    expire = create_time + effective_time_seconds

    # 1. Build the token info JSON (the part that gets signed + encrypted).
    token_info = {
        "app_id": app_id,
        "user_id": user_id,
        "nonce": nonce,
        "ctime": create_time,
        "expire": expire,
        "payload": payload or "",
    }
    plaintext = json.dumps(token_info, separators=(",", ":")).encode("utf-8")

    # 2. AES-CBC encrypt with a key derived from the server secret.
    key = server_secret.encode("utf-8")           # 32 bytes -> AES-256
    iv = os.urandom(16)
    encrypted = _aes_encrypt(plaintext, key, iv)

    # 3. Pack: [expire(8, big-endian)] [iv_len(2)] [iv] [cipher_len(2)] [cipher]
    packed = struct.pack(">q", expire)
    packed += struct.pack(">H", len(iv)) + iv
    packed += struct.pack(">H", len(encrypted)) + encrypted

    # 4. Version prefix "04" + base64 of the packed binary.
    return "04" + base64.b64encode(packed).decode("utf-8")


def build_room_privilege_payload(room_id: str, can_publish: bool = True) -> str:
    """
    Build the payload for a user-privilege token scoped to a single room.

    Prevents the 'ghost microphone' problem (non-seat users being heard) and
    stops a cracked client from logging into a different room ID. Used for
    voice rooms where seat/publish consistency matters.
    """
    privilege = {
        str(PRIVILEGE_LOGIN): 1,
        str(PRIVILEGE_PUBLISH): 1 if can_publish else 0,
    }
    payload = {
        "room_id": room_id,
        "privilege": privilege,
        "stream_id_list": None,
    }
    return json.dumps(payload, separators=(",", ":"))
