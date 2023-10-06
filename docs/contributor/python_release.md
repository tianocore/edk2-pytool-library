# Python Releases and edk2toollib

This document provides information on the necessary steps to update the
edk2-pytool-library repository when a new minor version of python has been
released (3.9, 3.10, etc).

## Steps

Each individual step will be a different section below and be associated with
a specific file that must be updated.

### pyproject.toml

This file is responsible for the release process to pypi. We want to make sure
we keep the required version for our pypi releases up to date. Update
`requires-python` to the minimum required python.

We typically support the last three minor versions; barring any special
exceptions, if the newest minor version is 3.11, then overall we will support
3.9, 3.10, and 3.11. Therefore you should update the line to
`python-requires = ">=3.9"`.

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

### bug_report.yml

Update the supported python versions in the entry with `id: py_version`

### VariableProducer.yml

Update `pythonversions` to the support versions

### readme.md

Update the python versions in the `Current Status` section
