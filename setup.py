#!/usr/bin/env python

import os, glob
from setuptools import setup, find_packages

install_requires = [line.rstrip() for line in open(os.path.join(os.path.dirname(__file__), "requirements.txt"))]

setup(
    name="hca",
    version="4.1.2",
    url='https://github.com/HumanCellAtlas/dcp-cli',
    license='Apache Software License',
    author='Human Cell Atlas contributors',
    author_email='akislyuk@chanzuckerberg.com',
    description='Human Cell Atlas Data Storage System Command Line Interface',
    long_description=open('README.rst').read(),
    install_requires=install_requires,
    extras_require={
        ':python_version == "2.7"': [
            'enum34 >= 1.1.6, < 2',
            'funcsigs >= 1.0.2, < 2',
            'pyopenssl >= 17.5.0'
        ],
        ':python_version < "3.5"': ['typing >= 3.6.2, < 4'],
    },
    packages=find_packages(exclude=['test']),
    scripts=glob.glob('scripts/*'),
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
