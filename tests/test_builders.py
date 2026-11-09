"""Tests for the request builders and the requests the wrappers send."""
from __future__ import annotations

from collections.abc import Iterator, Mapping
import contextlib
import http.server
import io
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import threading
from typing import Any, Callable
from unittest import mock
from urllib.parse import urlencode

import pytest
import requests

import gpsoauth

EMAIL = "someone@example.com"
ANDROID_ID = "0123456789abcdef"
SIGNATURE = b"invented-signature"
SIG = "38918a453d07199354f8b19af05ec6562ced5788"
PROXY = {"https": "http://proxy.invalid:3128"}
OPTIONS = {
    "service": "sj",
    "device_country": "gb",
    "operator_country": "de",
    "lang": "fr",
    "sdk_version": 30,
}
Fields = list[tuple[str, Any]]


def _master_fields(credentials: Fields, **options: Any) -> Fields:
    return [
        ("accountType", "HOSTED_OR_GOOGLE"),
        ("Email", EMAIL),
        ("has_permission", 1),
        ("add_account", 1),
        *credentials,
        ("service", options.get("service", "ac2dm")),
        ("source", "android"),
        ("androidId", ANDROID_ID),
        ("device_country", options.get("device_country", "us")),
        ("operatorCountry", options.get("operator_country", "us")),
        ("lang", options.get("lang", "en")),
        ("sdk_version", options.get("sdk_version", 17)),
        ("google_play_services_version", 240913000),
        ("client_sig", options.get("client_sig", SIG)),
        ("callerSig", options.get("client_sig", SIG)),
        ("droidguard_results", "dummy123"),
    ]


def _oauth_fields(**options: Any) -> Fields:
    return [
        ("accountType", "HOSTED_OR_GOOGLE"),
        ("Email", EMAIL),
        ("has_permission", 1),
        ("EncryptedPasswd", "aas_et/invented"),
        ("service", options.get("service", "oauth2:invented")),
        ("source", "android"),
        ("androidId", ANDROID_ID),
        ("app", "com.example.app"),
        ("client_sig", "invented-client-sig"),
        ("device_country", options.get("device_country", "us")),
        ("operatorCountry", options.get("operator_country", "us")),
        ("lang", options.get("lang", "en")),
        ("sdk_version", options.get("sdk_version", 17)),
        ("google_play_services_version", 240913000),
    ]


PASSWORD = [("EncryptedPasswd", SIGNATURE)]
TOKEN = [("ACCESS_TOKEN", 1), ("Token", "oauth2_4/invented")]
# (wrapper, builder, arguments, keyword arguments, expected form fields)
CASES = [
    pytest.param(
        gpsoauth.perform_master_login,
        gpsoauth.build_master_login_data,
        (EMAIL, "apassword", ANDROID_ID),
        {},
        _master_fields(PASSWORD),
        id="master-login-defaults",
    ),
    pytest.param(
        gpsoauth.perform_master_login,
        gpsoauth.build_master_login_data,
        (EMAIL, "apassword", ANDROID_ID),
        {**OPTIONS, "client_sig": "invented-sig"},
        _master_fields(PASSWORD, **OPTIONS, client_sig="invented-sig"),
        id="master-login-options",
    ),
    pytest.param(
        gpsoauth.exchange_token,
        gpsoauth.build_exchange_token_data,
        (EMAIL, "oauth2_4/invented", ANDROID_ID),
        {},
        _master_fields(TOKEN),
        id="exchange-token-defaults",
    ),
    pytest.param(
        gpsoauth.exchange_token,
        gpsoauth.build_exchange_token_data,
        (EMAIL, "oauth2_4/invented", ANDROID_ID),
        {**OPTIONS, "client_sig": "invented-sig"},
        _master_fields(TOKEN, **OPTIONS, client_sig="invented-sig"),
        id="exchange-token-options",
    ),
    pytest.param(
        gpsoauth.perform_oauth,
        gpsoauth.build_oauth_data,
        (EMAIL, "aas_et/invented", ANDROID_ID, "oauth2:invented"),
        {"app": "com.example.app", "client_sig": "invented-client-sig"},
        _oauth_fields(),
        id="oauth-defaults",
    ),
    pytest.param(
        gpsoauth.perform_oauth,
        gpsoauth.build_oauth_data,
        (EMAIL, "aas_et/invented", ANDROID_ID),
        {**OPTIONS, "app": "com.example.app", "client_sig": "invented-client-sig"},
        _oauth_fields(**OPTIONS),
        id="oauth-options",
    ),
]


@pytest.fixture(name="signature")
def fixture_signature() -> Iterator[mock.Mock]:
    """Make the randomized EncryptedPasswd predictable."""
    with mock.patch(
        "gpsoauth.google.construct_signature", return_value=SIGNATURE
    ) as signature:
        yield signature


@pytest.fixture(name="no_proxy_env")
def fixture_no_proxy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stop the host's proxy variables from reaching requests."""
    for name in list(os.environ):
        if name.lower().endswith("_proxy"):
            monkeypatch.delenv(name)


@pytest.mark.parametrize("_wrapper,builder,args,kwargs,expected", CASES)
def test_build_data(
    signature: mock.Mock,
    _wrapper: Callable[..., dict[str, str]],
    builder: Callable[..., dict[str, int | str | bytes]],
    args: tuple[str, ...],
    kwargs: dict[str, Any],
    expected: Fields,
) -> None:
    """Each builder returns the form fields of its wrapper, in order."""
    data = builder(*args, **kwargs)
    assert list(data.items()) == expected
    if builder is gpsoauth.build_master_login_data:
        signature.assert_called_once_with(
            EMAIL, "apassword", gpsoauth.ANDROID_KEY_7_3_29
        )
    assert builder(*args, **kwargs) is not data


def test_build_auth_headers() -> None:
    """The headers gpsoauth sets, with the current USER_AGENT, in a new dict."""
    headers = gpsoauth.build_auth_headers()
    assert headers == {
        "Accept-Encoding": "identity",
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": "GoogleAuth/1.4",
    }
    assert gpsoauth.build_auth_headers() is not headers
    with mock.patch.object(gpsoauth, "USER_AGENT", "invented/1.0"):
        assert gpsoauth.build_auth_headers()["User-Agent"] == "invented/1.0"


@pytest.mark.usefixtures("signature", "no_proxy_env")
@pytest.mark.parametrize("wrapper,_builder,args,kwargs,expected", CASES)
def test_wrapper_request(
    wrapper: Callable[..., dict[str, str]],
    _builder: Callable[..., dict[str, int | str | bytes]],
    args: tuple[str, ...],
    kwargs: dict[str, Any],
    expected: Fields,
) -> None:
    """Each wrapper posts its form fields with gpsoauth's headers and proxy.

    It looks AuthHTTPAdapter up when sending, so other code can replace it.
    """
    sent: list[tuple[requests.PreparedRequest, Mapping[str, str] | None]] = []

    class RecordingAdapter(gpsoauth.AuthHTTPAdapter):
        """Records the request instead of sending it."""

        def send(
            self, request: requests.PreparedRequest, *_args: Any, **kwargs: Any
        ) -> requests.Response:
            sent.append((request, kwargs["proxies"]))
            response = requests.Response()
            response.status_code = 200
            response.raw = io.BytesIO(b"Token=invented\n")
            return response

    with mock.patch.object(
        gpsoauth, "AuthHTTPAdapter", RecordingAdapter
    ), mock.patch.object(  # Never reach Google if the replacement is ignored
        requests.adapters.HTTPAdapter, "send", side_effect=AssertionError
    ):
        assert wrapper(*args, **kwargs, proxy=PROXY) == {"Token": "invented"}

    assert len(sent) == 1
    request, proxies = sent[0]
    body = urlencode(expected)
    assert (request.method, request.url, request.body) == (
        "POST",
        "https://android.clients.google.com/auth",
        body,
    )
    assert list(request.headers.items()) == [
        ("User-Agent", "GoogleAuth/1.4"),
        ("Accept-Encoding", "identity"),
        ("Accept", "*/*"),
        ("Connection", "keep-alive"),
        ("Content-type", "application/x-www-form-urlencoded"),
        ("Content-Length", str(len(body))),
    ]
    assert proxies == PROXY


HOST = "localnode.example.test"
# Invented certificates: file name, then the name they are for. The file
# names avoid "*", which Windows doesn't allow.
CERTIFICATES = {
    "matching": HOST,
    "partial-wildcard": "local*.example.test",
    "mismatch": "different.example.test",
}


@pytest.fixture(name="certificates", scope="module")
def fixture_certificates(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Invented self-signed certificates, named as in CERTIFICATES."""
    if not shutil.which("openssl"):
        pytest.skip("needs the openssl command")
    directory = tmp_path_factory.mktemp("certificates")
    for name, san in CERTIFICATES.items():
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1"]
            + ["-subj", "/CN=invented", "-addext", f"subjectAltName=DNS:{san}"]
            + ["-keyout", str(directory / f"{name}.key")]
            + ["-out", str(directory / f"{name}.pem")],
            check=True,
            capture_output=True,
        )
    return directory


class _AuthHandler(http.server.BaseHTTPRequestHandler):
    """Answers a POST like a successful login."""

    timeout = 5

    def do_POST(self) -> None:  # pylint: disable=invalid-name
        """Read the request and answer with a token."""
        self.rfile.read(int(self.headers["Content-Length"]))
        body = b"Token=invented\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@contextlib.contextmanager
def _tls_server(
    certificates: Path, name: str, monkeypatch: pytest.MonkeyPatch
) -> Iterator[int]:
    """Serve one connection on 127.0.0.1 with the named certificate.

    The certificate is the only one trusted by load_default_certs().
    """
    monkeypatch.setenv("SSL_CERT_FILE", str(certificates / f"{name}.pem"))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificates / f"{name}.pem", certificates / f"{name}.key")
    context.set_alpn_protocols(["http/1.1"])
    with http.server.HTTPServer(("127.0.0.1", 0), _AuthHandler) as server:
        server.socket = context.wrap_socket(server.socket, server_side=True)
        server.timeout = 5
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            yield server.server_address[1]
        finally:
            thread.join()


@pytest.mark.usefixtures("no_proxy_env")
@pytest.mark.parametrize(
    "name,accepted",
    [
        ("matching", True),
        # urllib3 accepts partial wildcards, Python's ssl module doesn't: the
        # wrappers keep urllib3's check.
        ("partial-wildcard", True),
        ("mismatch", False),
    ],
)
def test_wrapper_checks_hostname(
    certificates: Path, monkeypatch: pytest.MonkeyPatch, name: str, accepted: bool
) -> None:
    """The wrappers accept the certificates urllib3 accepts for the host."""
    resolve = socket.getaddrinfo

    def local(_host: str, *args: Any, **kwargs: Any) -> Any:
        return resolve("127.0.0.1", *args, **kwargs)

    with _tls_server(certificates, name, monkeypatch) as port:
        monkeypatch.setattr(gpsoauth, "AUTH_URL", f"https://{HOST}:{port}/auth")
        monkeypatch.setattr(socket, "getaddrinfo", local)
        if accepted:
            assert gpsoauth.perform_oauth(
                EMAIL, "aas_et/invented", ANDROID_ID, "service", "app", "sig"
            ) == {"Token": "invented"}
        else:
            with pytest.raises(requests.exceptions.SSLError):
                gpsoauth.perform_oauth(
                    EMAIL, "aas_et/invented", ANDROID_ID, "service", "app", "sig"
                )


@pytest.mark.parametrize("name,accepted", [("matching", True), ("mismatch", False)])
def test_ssl_context_checks_hostname(
    certificates: Path, monkeypatch: pytest.MonkeyPatch, name: str, accepted: bool
) -> None:
    """The context checks the hostname itself, without urllib3, and sends no ALPN."""
    with _tls_server(certificates, name, monkeypatch) as port:
        context = gpsoauth.create_ssl_context()
        context.set_alpn_protocols(["http/1.1"])
        with socket.create_connection(("127.0.0.1", port)) as sock:
            if accepted:
                with context.wrap_socket(sock, server_hostname=HOST) as tls:
                    assert tls.selected_alpn_protocol() is None
            else:
                with pytest.raises(ssl.SSLCertVerificationError):
                    context.wrap_socket(sock, server_hostname=HOST)


@pytest.mark.filterwarnings("error::DeprecationWarning")
def test_ssl_context_settings() -> None:
    """A new context each time, checking certificates, with session tickets.

    Creating it raises no DeprecationWarning, such as those of SSLContext()
    without a protocol.
    """
    context = gpsoauth.create_ssl_context()
    assert isinstance(context, gpsoauth.SSLContext)
    assert context is not gpsoauth.create_ssl_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
    assert not context.options & ssl.OP_NO_TICKET  # pylint: disable=no-member


def _cipher_names(context: ssl.SSLContext, tls13: bool) -> list[str]:
    return [
        cipher["name"]
        for cipher in context.get_ciphers()
        if (cipher["protocol"] == "TLSv1.3") == tls13
    ]


def test_ssl_context_ciphers() -> None:
    """With urllib3 < 2, use its ciphers; set_ciphers() leaves TLS 1.3 alone."""
    baseline = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    cipher = "ECDHE-RSA-AES128-GCM-SHA256"
    with mock.patch.object(gpsoauth, "SSL_DEFAULT_CIPHERS", cipher):
        context = gpsoauth.create_ssl_context()
    assert _cipher_names(context, tls13=False) == [cipher]
    assert _cipher_names(context, tls13=True) == _cipher_names(baseline, tls13=True)

    with mock.patch.object(gpsoauth, "SSL_DEFAULT_CIPHERS", None):
        context = gpsoauth.create_ssl_context()
    assert context.get_ciphers() == baseline.get_ciphers()
