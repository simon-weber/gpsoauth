gpsoauth: a python client library for Google Play Services OAuth
================================================================

.. image:: https://img.shields.io/badge/dynamic/json.svg?label=release&query=%24.status&maxAge=43200&uri=https%3A%2F%2Fwww.repominder.com%2Fbadge%2FeyJmdWxsX25hbWUiOiAic2ltb24td2ViZXIvZ3Bzb2F1dGgifQ%3D%3D%2F&link=https%3A%2F%2Fwww.repominder.com%2F
    :target: https://www.repominder.com   

gpsoauth allows python code to use the "master token" flow that KB Sriram described at http://sbktech.blogspot.com/2014/01/inside-android-play-services-magic.html.

This can be useful when writing code that poses as a Google app, like `gmusicapi does here <https://github.com/simon-weber/gmusicapi/blob/87a802ab3a59a7fa2974fd9755d59a55275484d9/gmusicapi/session.py#L267-L278>`__.

Many thanks to Dima Kovalenko for reverse engineering the EncryptedPasswd signature in http://codedigging.com/blog/2014-06-09-about-encryptedpasswd.

Ports
-----
* C#: https://github.com/vemacs/GPSOAuthSharp.
* Ruby: https://github.com/bryanmytko/gpsoauth
* Java: https://github.com/svarzee/gpsoauth-java
* C++: https://github.com/dvirtz/gpsoauth-cpp and https://github.com/Iciclelz/gpsoauthclient
