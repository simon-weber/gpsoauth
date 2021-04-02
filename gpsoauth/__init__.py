"""A python client library for Google Play Services OAuth."""
import ssl

from importlib_metadata import version
import requests
from urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import DEFAULT_CIPHERS

from . import google

__version__ = version(__package__)

# The key is distirbuted with Google Play Services.
# This one is from version 7.3.29.
B64_KEY_7_3_29 = (
    b"AAAAgMom/1a/v0lblO2Ubrt60J2gcuXSljGFQXgcyZWveWLEwo6prwgi3"
    b"iJIZdodyhKZQrNWp5nKJ3srRXcUW+F1BD3baEVGcmEgqaLZUNBjm057pK"
    b"RI16kB0YppeGx5qIQ5QjKzsR8ETQbKLNWgRY0QRNVz34kMJR3P/LgHax/"
    b"6rmf5AAAAAwEAAQ=="
)

ANDROID_KEY_7_3_29 = google.key_from_b64(B64_KEY_7_3_29)

AUTH_URL = "https://android.clients.google.com/auth"
USER_AGENT = "gpsoauth/" + __version__

# Blocking AESCCM in urllib3 > 1.26.3 causes Google to return 403 Bad
# Authentication.
CIPHERS = ":".join(
    cipher for cipher in DEFAULT_CIPHERS.split(":") if cipher != "!AESCCM"
)


class SSLContext(ssl.SSLContext):
    """SSLContext wrapper."""

    def set_alpn_protocols(self, alpn_protocols):
        """
        ALPN headers cause Google to return 403 Bad Authentication.
        """


class AuthHTTPAdapter(requests.adapters.HTTPAdapter):
    """HTTPAdapter wrapper."""

    def init_poolmanager(self, *args, **kwargs):
        """
        Secure settings from ssl.create_default_context(), but without
        ssl.OP_NO_TICKET which causes Google to return 403 Bad
        Authentication.
        """
        context = SSLContext()
        context.set_ciphers(CIPHERS)
        context.options |= ssl.OP_NO_COMPRESSION
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.post_handshake_auth = True
        context.verify_mode = ssl.CERT_REQUIRED
        self.poolmanager = PoolManager(*args, ssl_context=context, **kwargs)


def _perform_auth_request(data, proxy=None):
    session = requests.session()
    session.mount(AUTH_URL, AuthHTTPAdapter())
    if proxy:
        session.proxies = proxy

    res = session.post(AUTH_URL, data, headers={"User-Agent": USER_AGENT})

    return google.parse_auth_response(res.text)


def perform_master_login(
    email,
    password,
    android_id,
    service="ac2dm",
    device_country="us",
    operator_country="us",
    lang="en",
    sdk_version=17,
    proxy=None,
):
    """
    Perform a master login, which is what Android does when you first add
    a Google account.

    Return a dict, eg::

        {
            'Auth': '...',
            'Email': 'email@gmail.com',
            'GooglePlusUpgrade': '1',
            'LSID': '...',
            'PicasaUser': 'My Name',
            'RopRevision': '1',
            'RopText': ' ',
            'SID': '...',
            'Token': 'oauth2rt_1/...',
            'firstName': 'My',
            'lastName': 'Name',
            'services': 'hist,mail,googleme,...'
        }
    """

    data = {
        "accountType": "HOSTED_OR_GOOGLE",
        "Email": email,
        "has_permission": 1,
        "add_account": 1,
        "EncryptedPasswd": google.construct_signature(
            email, password, ANDROID_KEY_7_3_29
        ),
        "service": service,
        "source": "android",
        "androidId": android_id,
        "device_country": device_country,
        "operatorCountry": operator_country,
        "lang": lang,
        "sdk_version": sdk_version,
    }

    return _perform_auth_request(data, proxy)


def perform_oauth(
    email,
    master_token,
    android_id,
    service,
    app,
    client_sig,
    device_country="us",
    operator_country="us",
    lang="en",
    sdk_version=17,
    proxy=None,
):
    """
    Use a master token from master_login to perform OAuth to a specific Google service.

    Return a dict, eg::

        {
            'Auth': '...',
            'LSID': '...',
            'SID': '..',
            'issueAdvice': 'auto',
            'services': 'hist,mail,googleme,...'
        }

    To authenticate requests to this service, include a header
    ``Authorization: GoogleLogin auth=res['Auth']``.
    """

    data = {
        "accountType": "HOSTED_OR_GOOGLE",
        "Email": email,
        "has_permission": 1,
        "EncryptedPasswd": master_token,
        "service": service,
        "source": "android",
        "androidId": android_id,
        "app": app,
        "client_sig": client_sig,
        "device_country": device_country,
        "operatorCountry": operator_country,
        "lang": lang,
        "sdk_version": sdk_version,
    }

    return _perform_auth_request(data, proxy)
