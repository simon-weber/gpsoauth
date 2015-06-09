gpsoauth: a python client library for Google Play Services OAuth
================================================================

gpsoauth allows python code to use the "master token" flow that KB Sriram described at http://sbktech.blogspot.com/2014/01/inside-android-play-services-magic.html.

This can be useful when writing code that poses as a Google app, like `gmusicapi <https://github.com/simon-weber/Unofficial-Google-Music-API>`__ does.

Many thanks to Dima Kovalenko for reverse engieering the EncryptedPasswd signature in http://codedigging.com/blog/2014-06-09-about-encryptedpasswd.

Ports
-----
* C#: https://github.com/vemacs/GPSOAuthSharp.
