from __future__ import unicode_literals

import re
from setuptools import setup, find_packages


def get_version(filename):
    content = open(filename).read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", content))
    return metadata['version']

setup(
    name='Mopidy-Subsonic',
    version=get_version('mopidy_subsonic/__init__.py'),
    url='http://github.com/rattboi/mopidy-subsonic/',
    license='MIT',
    author='rattboi',
    author_email='rattboi@gmail.com',
    description='Subsonic extension for Mopidy',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy',
        'py-sonic',
    ],
    entry_points={
        b'mopidy.ext': [
            'subsonic = mopidy_subsonic:SubsonicExtension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
