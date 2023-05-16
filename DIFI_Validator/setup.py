from setuptools import setup
test_deps = ['pytest']
extras = {
    'test': test_deps
}
setup(
    name='difi_utils',
    version="0.1",
    description='Utilities for working with DIFI packets',
    long_description="",
    author='DIFI Consortium',
    zip_safe=False,
    classifiers=["Programming Language :: Python :: 3"],
    tests_require=test_deps,
    extras_require=extras,
    packages=['difi_utils'],
    include_package_data=True,
)