#!/usr/bin/python3

#import setuptools
from distutils.core import setup


#import os.path
#import warnings
#import sys


setup(
    name='b2p',
    version='2021-06-06',
    description='stream trorrent',
    long_description='fork',
    url='https://github.com/acroobat/b2p',
    author='Roman Beslik',
    author_email='rabeslik@gmail.com',
    maintainer='acroobat',
    maintainer_email='acroobat@mail.ru',
    license='LGPL',
    packages=['b2p'],
    scripts=['bin/b2p']
)
