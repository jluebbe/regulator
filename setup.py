#!/usr/bin/env python3
import fastentrypoints
from setuptools import find_packages
from setuptools import setup

setup(
    name='regulator',
    description='regulator: register dump decoder',
    author='Jan Luebbe',
    author_email='entwicklung@pengutronix.de',
    license='LGPL-2.1',
    use_scm_version=True,
    url='https://github.com/jluebbe/regulator',
    python_requires='>=3.5',
    setup_requires=[
        'pytest-runner',
        'setuptools_scm',
    ],
    tests_require=[
        'hypothesis',
    ],
    install_requires=[
        'attrs',
        'bitstruct',
        'click',
        'prettyprinter',
        'pygobject',
        'pyyaml',
        'sortedcontainers',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'regulator = regulator.__main__:cli',
        ]
    },
)
