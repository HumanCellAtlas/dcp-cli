#!/usr/bin/env python

import os
from setuptools import setup, find_packages

install_requires = [line.rstrip() for line in open(os.path.join(os.path.dirname(__file__), "requirements.txt"))]

setup(
    name="hca",
    version='7.0.1',
    url='https://github.com/HumanCellAtlas/dcp-cli',
    license='Apache Software License',
    author='Human Cell Atlas contributors',
    author_email='akislyuk@chanzuckerberg.com',
    description='Human Cell Atlas Data Storage System Command Line Interface',
    long_description=open('README.rst').read(),
    install_requires=install_requires,
    extras_require={
        ':python_version < "3.5"': [
            'typing >= 3.6.2, < 4',
            'scandir >= 1.9.0, < 2'
        ],
    },
    packages=find_packages(exclude=['test']),
    entry_points={
        'console_scripts': [
            'hca=hca.cli:main'
        ],
    },
    platforms=['MacOS X', 'Posix'],
    package_data={'hcacli': ['*.json']},
    zip_safe=False,
    include_package_data=True,
    test_suite='test',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
