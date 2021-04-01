"""Tests for gpsoauth."""
from gpsoauth import ANDROID_KEY_7_3_29, B64_KEY_7_3_29
from gpsoauth.google import construct_signature
from gpsoauth.util import bytes_to_int, int_to_bytes


def test_static_signature():
    """Test static signature."""
    username = "someone@google.com"
    password = "apassword"
    assert construct_signature(username, password, ANDROID_KEY_7_3_29).startswith(
        b"AFcb4K"
    )


def test_conversion_roundtrip():
    """Test key is the same after roundtrip conversion."""
    assert int_to_bytes(bytes_to_int(B64_KEY_7_3_29)) == B64_KEY_7_3_29
