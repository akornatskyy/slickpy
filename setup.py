import re

from setuptools import setup

README = open("README.md").read()
VERSION = (
    re.search(
        r"__version__ = \"(.+)\"", open("src/slickpy/__init__.py").read()
    )
    .group(1)
    .strip()
)

setup(
    name="slickpy",
    version=VERSION,
    python_requires=">=3.6",
    description="A lightweight ASGI toolkit, optimized for great performance, "
    "flexibility and productivity.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/akornatskyy/slickpy",
    author="Andriy Kornatskyy",
    author_email="andriy.kornatskyy@live.com",
    license="MIT",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ASGI http web toolkit",
    packages=["slickpy", "slickpy.middleware"],
    package_data={"slickpy": ["py.typed"]},
    package_dir={"": "src"},
    zip_safe=True,
    install_requires=[],
    platforms="any",
)
