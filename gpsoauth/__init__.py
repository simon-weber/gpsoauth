"""A python client library for Google Play Services OAuth."""
from __future__ import annotations

from collections.abc import MutableMapping
from importlib.metadata import version
import ssl
from typing import Any, Iterable

import requests
from urllib3.poolmanager import PoolManager

from . import google

SSL_DEFAULT_CIPHERS = None
if version("urllib3") < "2.0.0a1":
    # pylint: disable-next=no-name-in-module
    from urllib3.util.ssl_ import DEFAULT_CIPHERS

    SSL_DEFAULT_CIPHERS = DEFAULT_CIPHERS


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
USER_AGENT = "GoogleAuth/1.4"

# Google is very picky about list of used ciphers. Changing this list most likely
# will cause BadAuthentication error.
CIPHERS = [
    "ECDHE+AESGCM",
    "ECDHE+CHACHA20",
    "DHE+AESGCM",
    "DHE+CHACHA20",
    "ECDH+AES",
    "DH+AES",
    "RSA+AESGCM",
    "RSA+AES",
    "!aNULL",
    "!eNULL",
    "!MD5",
    "!DSS",
]


class SSLContext(ssl.SSLContext):
    """SSLContext wrapper."""

    def set_alpn_protocols(self, alpn_protocols: Iterable[str]) -> None:
        """
        ALPN headers cause Google to return 403 Bad Authentication.
        """


def create_ssl_context() -> ssl.SSLContext:
    """
    Return a new SSL context with the TLS settings gpsoauth uses for AUTH_URL.

    It is built as the one gpsoauth's own requests use: a client context
    (PROTOCOL_TLS_CLIENT), with urllib3's ciphers if urllib3 < 2. It requires a
    valid certificate for the server's hostname and trusts the system's
    certificate authorities. Unlike urllib3's default context, it allows TLS
    session tickets, and unlike urllib3's and aiohttp's, it offers no ALPN
    (its set_alpn_protocols() does nothing): Google returns 403 Bad
    Authentication if tickets are disabled or ALPN is offered.

    gpsoauth's own functions may also trust the CA bundle requests uses,
    depending on its version and settings: certifi's, or the file named by
    REQUESTS_CA_BUNDLE or CURL_CA_BUNDLE. To trust the same certificates, add
    that bundle with the context's load_verify_locations().

    Loading certificates blocks, so in async code create the context once,
    outside the event loop, and add any bundle there too.
    """
    context = SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if SSL_DEFAULT_CIPHERS:
        context.set_ciphers(SSL_DEFAULT_CIPHERS)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.options &= ~ssl.OP_NO_TICKET  # pylint: disable=E1101
    context.load_default_certs()
    return context


class AuthHTTPAdapter(requests.adapters.HTTPAdapter):
    """TLS tweaks."""

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
        """Use the TLS settings of create_ssl_context()."""
        context = create_ssl_context()
        # Leave the hostname check to urllib3, as gpsoauth always has: its
        # matching differs from the ssl module's, e.g. for partial wildcards.
        context.check_hostname = False
        self.poolmanager = PoolManager(*args, ssl_context=context, **kwargs)


def build_auth_headers() -> dict[str, str]:
    """
    Return the headers gpsoauth sets on its requests to AUTH_URL.

    HTTP clients add their own default headers to these, such as Accept.
    """
    return {
        "Accept-Encoding": "identity",
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": USER_AGENT,
    }


def _perform_auth_request(
    data: dict[str, int | str | bytes], proxies: MutableMapping[str, str] | None = None
) -> dict[str, str]:
    session = requests.session()
    session.mount(AUTH_URL, AuthHTTPAdapter())
    if proxies:
        session.proxies = proxies
    session.headers.update(build_auth_headers())

    res = session.post(AUTH_URL, data=data, verify=True)

    return google.parse_auth_response(res.text)


def build_master_login_data(
    email: str,
    password: str,
    android_id: str,
    service: str = "ac2dm",
    device_country: str = "us",
    operator_country: str = "us",
    lang: str = "en",
    sdk_version: int = 17,
    client_sig: str = "38918a453d07199354f8b19af05ec6562ced5788",
) -> dict[str, int | str | bytes]:
    """
    Return the form fields perform_master_login() posts to AUTH_URL, as a new dict.

    It takes the same arguments, except proxy. EncryptedPasswd differs on each
    call, as the encryption is randomized.
    """
    return {
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
        "google_play_services_version": 240913000,
        "client_sig": client_sig,
        "callerSig": client_sig,
        "droidguard_results": "dummy123",
    }


def perform_master_login(
    email: str,
    password: str,
    android_id: str,
    service: str = "ac2dm",
    device_country: str = "us",
    operator_country: str = "us",
    lang: str = "en",
    sdk_version: int = 17,
    proxy: MutableMapping[str, str] | None = None,
    client_sig: str = "38918a453d07199354f8b19af05ec6562ced5788",
) -> dict[str, str]:
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

    data = build_master_login_data(
        email,
        password,
        android_id,
        service=service,
        device_country=device_country,
        operator_country=operator_country,
        lang=lang,
        sdk_version=sdk_version,
        client_sig=client_sig,
    )

    return _perform_auth_request(data, proxy)


def build_exchange_token_data(
    email: str,
    token: str,
    android_id: str,
    service: str = "ac2dm",
    device_country: str = "us",
    operator_country: str = "us",
    lang: str = "en",
    sdk_version: int = 17,
    client_sig: str = "38918a453d07199354f8b19af05ec6562ced5788",
) -> dict[str, int | str | bytes]:
    """
    Return the form fields exchange_token() posts to AUTH_URL, as a new dict.

    It takes the same arguments, except proxy.
    """
    return {
        "accountType": "HOSTED_OR_GOOGLE",
        "Email": email,
        "has_permission": 1,
        "add_account": 1,
        "ACCESS_TOKEN": 1,
        "Token": token,
        "service": service,
        "source": "android",
        "androidId": android_id,
        "device_country": device_country,
        "operatorCountry": operator_country,
        "lang": lang,
        "sdk_version": sdk_version,
        "google_play_services_version": 240913000,
        "client_sig": client_sig,
        "callerSig": client_sig,
        "droidguard_results": "dummy123",
    }


def exchange_token(
    email: str,
    token: str,
    android_id: str,
    service: str = "ac2dm",
    device_country: str = "us",
    operator_country: str = "us",
    lang: str = "en",
    sdk_version: int = 17,
    proxy: MutableMapping[str, str] | None = None,
    client_sig: str = "38918a453d07199354f8b19af05ec6562ced5788",
) -> dict[str, str]:
    """
    Exchanges a web oauth_token for a master token.

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

    data = build_exchange_token_data(
        email,
        token,
        android_id,
        service=service,
        device_country=device_country,
        operator_country=operator_country,
        lang=lang,
        sdk_version=sdk_version,
        client_sig=client_sig,
    )

    return _perform_auth_request(data, proxy)


def build_oauth_data(
    email: str,
    master_token: str,
    android_id: str,
    service: str,
    app: str,
    client_sig: str,
    device_country: str = "us",
    operator_country: str = "us",
    lang: str = "en",
    sdk_version: int = 17,
) -> dict[str, int | str | bytes]:
    """
    Return the form fields perform_oauth() posts to AUTH_URL, as a new dict.

    It takes the same arguments, except proxy.
    """
    return {
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
        "google_play_services_version": 240913000,
    }


def perform_oauth(
    email: str,
    master_token: str,
    android_id: str,
    service: str,
    app: str,
    client_sig: str,
    device_country: str = "us",
    operator_country: str = "us",
    lang: str = "en",
    sdk_version: int = 17,
    proxy: MutableMapping[str, str] | None = None,
) -> dict[str, str]:
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

    data = build_oauth_data(
        email,
        master_token,
        android_id,
        service=service,
        app=app,
        client_sig=client_sig,
        device_country=device_country,
        operator_country=operator_country,
        lang=lang,
        sdk_version=sdk_version,
    )

    return _perform_auth_request(data, proxy)
