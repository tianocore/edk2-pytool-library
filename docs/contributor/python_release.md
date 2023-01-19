# Python Releases and edk2toollib

This document provides information on the necessary steps to update the
edk2-pytool-library repository when a new minor version of python has been
released (3.9, 3.10, etc).

## Steps

Each individual step will be a different section below and be associated with
a specific file that must be updated.

### setup.py

This file is responsible for the release process to pypi. We want to make sure
we keep the required version for our pypi releases up to date. Within
`setuptools.setup()` locate the line `python_requires = "XXX"` and update it to
the next version.

We typically support the last three minor versions; barring any special
exceptions, if the newest minor version is 3.11, then overall we will support
3.9, 3.10, and 3.11. Therefore you should update the line to
`python_requires = ">=3.9.0"`.

Additionally, we must update the classifiers section to show the three
supported python versions:

```python
classifiers=[
    ...
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11"
]
```
