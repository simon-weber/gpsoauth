# gpsoauth

[![CI](https://github.com/simon-weber/gpsoauth/actions/workflows/ci.yaml/badge.svg)](https://github.com/simon-weber/gpsoauth/actions/workflows/ci.yaml)
[![PyPI version](https://badge.fury.io/py/gpsoauth.svg)](https://pypi.org/project/gpsoauth/)
[![repominder](https://img.shields.io/badge/dynamic/json.svg?label=release&query=%24.status&maxAge=43200&uri=https%3A%2F%2Fwww.repominder.com%2Fbadge%2FeyJmdWxsX25hbWUiOiAic2ltb24td2ViZXIvZ3Bzb2F1dGgifQ%3D%3D%2F&link=https%3A%2F%2Fwww.repominder.com%2F)](https://www.repominder.com)

**Python client library for Google Play Services OAuth.**

`gpsoauth` allows python code to use the "master token" flow that KB Sriram described at
<http://sbktech.blogspot.com/2014/01/inside-android-play-services-magic.html>.

```python
import gpsoauth

email = 'example@gmail.com'
password = 'my-password'
android_id = '0123456789abcdef'

master_response = gpsoauth.perform_master_login(email, password, android_id)
master_token = master_response['Token']

auth_response = gpsoauth.perform_oauth(
    email, master_token, android_id,
    service='sj', app='com.google.android.music',
    client_sig='...')
token = auth_response['Auth']
```

This can be useful when writing code that poses as a Google app, like
[gmusicapi does here](https://github.com/simon-weber/gmusicapi/blob/87a802ab3a59a7fa2974fd9755d59a55275484d9/gmusicapi/session.py#L267-L278).

Many thanks to Dima Kovalenko for reverse engineering the EncryptedPasswd signature in
<https://web.archive.org/web/20150814054004/http://codedigging.com/blog/2014-06-09-about-encryptedpasswd/>.

For an explanation of recent changes, see [the changelog](https://github.com/simon-weber/gpsoauth/blob/master/CHANGELOG.md).

## Alternative flow

There is an alternative login flow if you are experiencing `BadAuthentication` errors.

1. Go to https://accounts.google.com/EmbeddedSetup
2. Log into your Google Account
3. Click on "I agree" when prompted. The page may show a loading screen forever; ignore it and move on to the next step.
4. Obtain the value of the `oauth_token` cookie. For more details see [the gpsoauth-java readme](https://github.com/rukins/gpsoauth-java/blob/b74ebca999d0f5bd38a2eafe3c0d50be552f6385/README.md#receiving-an-authentication-token).

Then, perform the token exchange:

```python
import gpsoauth

email = 'example@gmail.com'
android_id = '0123456789abcdef'
token = '...' # insert the oauth_token here

master_response = gpsoauth.exchange_token(email, token, android_id)
master_token = master_response['Token']  # if there's no token check the response for more details

auth_response = gpsoauth.perform_oauth(
    email, master_token, android_id,
    service='sj', app='com.google.android.music',
    client_sig='...')
token = auth_response['Auth']
```

## Ports

- C\#: <https://github.com/vemacs/GPSOAuthSharp>
- Ruby: <https://github.com/bryanmytko/gpsoauth>
- Java: <https://github.com/svarzee/gpsoauth-java>
- C++: <https://github.com/dvirtz/gpsoauth-cpp> and <https://github.com/Iciclelz/gpsoauthclient>

## Contributing

See [Contributing guidelines](https://github.com/simon-weber/gpsoauth/blob/master/CONTRIBUTING.md).
This is an open-source project and all contributions are highly welcomed.
