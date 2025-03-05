# Python Releases and edk2toollib

This document provides information on the necessary steps to update the
edk2-pytool-library repository when a new minor version of python has been
released (3.9, 3.10, etc).

## Steps

Each individual step will be a different section below and be associated with
a specific file that must be updated.

### pyproject.toml

We must update the classifiers section to show the new supported python version:

```python
classifiers=[
    ...
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13"
]
```

### bug_report.yml

Update the supported python versions in the entry with `id: py_version`

### VariableProducer.yml

Update `pythonversions` to the support versions

### readme.md

Update the python versions in the `Current Status` section
