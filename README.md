# SlickPy

![tests](https://github.com/akornatskyy/slickpy/workflows/tests/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/akornatskyy/slickpy/badge.svg?branch=master)](https://coveralls.io/github/akornatskyy/slickpy?branch=master)
[![pypi version](https://badge.fury.io/py/slickpy.svg)](https://badge.fury.io/py/slickpy)

A lightweight [ASGI](https://asgi.readthedocs.io/en/latest/index.html)
Python 3.6+ toolkit, optimized for great performance, flexibility and
productivity.

## Install

```sh
pip install slickpy
```

## Overview

*example.py*:

```python
from slickpy import App, Writer

app = App()


@app.route("/")
async def welcome(w: Writer) -> None:
    await w.end(b"Hello, world!")


main = app.asgi()
```

Then run the example with [uvicorn](https://github.com/encode/uvicorn):

```sh
uvicorn example:main
```

See [examples](https://github.com/akornatskyy/slickpy/tree/master/examples) for more.
