import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as f:
    readme = f.read()

# This hack is from http://stackoverflow.com/a/7071358/1231454;
# the version is kept in a seperate file and gets parsed - this
# way, setup.py doesn't have to import the package.

VERSIONFILE = 'gpsoauth/_version.py'

version_line = open(VERSIONFILE).read()
version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
match = re.search(version_re, version_line, re.M)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Could not find version in '%s'" % VERSIONFILE)

setup(
    name='gpsoauth',
    version=version,
    description='A python client library for Google Play Services OAuth.',
    long_description=readme,
    author='Simon Weber',
    author_email='simon@simonmweber.com',
    url='https://github.com/simon-weber/gpsoauth',
    packages=['gpsoauth'],
    include_package_data=True,
    install_requires=[
        'pycryptodomex >= 3.0',
        'requests',
    ],
    license='MIT',
    zip_safe=False,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ),
)
