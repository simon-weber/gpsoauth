"""Functions to work with Google authentication structures."""
import base64
import hashlib

from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

from .util import bytes_to_int, int_to_bytes


def key_from_b64(b64_key):
    """Extract key from base64."""
    binary_key = base64.b64decode(b64_key)

    i = bytes_to_int(binary_key[:4])
    mod = bytes_to_int(binary_key[4 : 4 + i])

    j = bytes_to_int(binary_key[i + 4 : i + 4 + 4])
    exponent = bytes_to_int(binary_key[i + 8 : i + 8 + j])

    key = RSA.construct((mod, exponent))

    return key


def key_to_struct(key):
    """Convert key to struct."""
    mod = int_to_bytes(key.n)
    exponent = int_to_bytes(key.e)

    return b"\x00\x00\x00\x80" + mod + b"\x00\x00\x00\x03" + exponent


def parse_auth_response(text):
    """Parse received auth response."""
    response_data = {}
    for line in text.split("\n"):
        if not line:
            continue

        key, _, val = line.partition("=")
        response_data[key] = val

    return response_data


def construct_signature(email, password, key):
    """Construct signature."""
    signature = bytearray(b"\x00")

    struct = key_to_struct(key)
    signature.extend(hashlib.sha1(struct).digest()[:4])

    cipher = PKCS1_OAEP.new(key)
    encrypted_login = cipher.encrypt((email + u"\x00" + password).encode("utf-8"))

    signature.extend(encrypted_login)

    return base64.urlsafe_b64encode(signature)
