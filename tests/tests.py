from gpsoauth.google import signature
from gpsoauth.util import bytes_to_long, long_to_bytes
from gpsoauth import android_key_7_3_29, b64_key_7_3_29


def test_static_signature():
    username = "someone@google.com"
    password = "apassword"
    assert signature(username, password, android_key_7_3_29).startswith(b"AFcb4K")


def test_conversion_roundtrip():
    assert long_to_bytes(bytes_to_long(b64_key_7_3_29)) == b64_key_7_3_29
