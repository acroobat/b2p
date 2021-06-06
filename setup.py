#!/usr/bin/python3
import setuptools

import os.path
import warnings
import sys

if setuptools_available:
        params['scripts'] = ['bin/b2p']

setup(
    name='b2p',
    version=__version__,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url='https://github.com/acroobat/youtube-dl',
    author='Roman Beslik',
    author_email='rabeslik@gmail.com',
    maintainer='acroobat',
    maintainer_email='acroobat@mail.ru',
    license='Unlicense',
    packages=[
        'b2p'],
)

