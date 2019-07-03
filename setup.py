from setuptools import setup, find_packages

test_deps = [
    'pytest',
    'pytest-asyncio',
    'python-coveralls',
    'pytest-cov',
    'codecov',
]

extras = {
    'test': test_deps,
}

setup(
    name='porkpepper',
    version='0.2.0',
    author='宋伟(songwei)',
    author_email='songwei@songwei.io',
    long_description='',
    url='https://github.com/xdusongwei/porkpepper',
    packages=find_packages(),
    ext_modules=[],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.7.0',
    install_requires=[
        'Jinja2',
        'base58',
        'aiotools',
        'aiohttp',
        'typing',
        'pytest',
        'aioredis',
    ],
    tests_require=test_deps,
    extras_require=extras,
)
