from setuptools import find_packages, setup

from brennivin import version, __author__, __email__, __license__, __url__

setup(
    name='brennivin',
    version=version,
    author=__author__,
    author_email=__email__,
    description="TBD",
    long_description=open('README.rst').read(),
    license=__license__,
    keywords='TBD TBD',
    url=__url__,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[]
)
