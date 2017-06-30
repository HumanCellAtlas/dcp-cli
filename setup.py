#!/usr/bin/env python

import glob
from setuptools import setup, find_packages

setup(
    name="hca-cli",
    version="0.1.0",
    url='https://github.com/HumanCellAtlas/data-store-cli',
    license='Apache Software License',
    author='Human Cell Atlas contributors',
    author_email='akislyuk@chanzuckerberg.com',
    description='Human Cell Atlas Data Storage System Command Line Interface',
    long_description=open('README.rst').read(),
    install_requires=[
        "requests==2.17.3",
        "jsonpointer==1.10",
        "boto3==1.4.4",
        "crcmod==1.7"
    ],
    extras_require={
        ':python_version == "2.7"': ['enum34 >= 1.1.6, < 2']
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
