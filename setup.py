#!/usr/bin/env python
from setuptools import find_packages, setup

setup(name='webmonitor',
      packages=find_packages(),
      include_package_data=True,
      version='1.0',
      description='Server for checking if given webpages contain required string',
      author='Piotr Szymanski',
      author_email='p.szymanski@bidpy.pl',
      url='https://github.com/eddwardo/webmonitor',
      install_requires=[i.strip() for i in open('requirements.txt').readlines()]
)
