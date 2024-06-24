# Tianocore Edk2 PyTool Library (edk2toollib)

[![pypi]][_pypi]
[![codecov]][_codecov]
[![ci]][_ci]
[![docs]][_docs]

This is a Tianocore maintained project consisting of a python library supporting
UEFI firmware development.  This package's intent is to provide an easy way to
organize and share python code to facilitate reuse across environments, tools,
and scripts.  Inclusion of this package and dependency management is best
managed using Pip/Pypi.

This is a supplemental package and is not required to be used for edk2 builds.

## Current Status

[![codecov]][_codecov]
[![ci]][_ci]

The code coverage and CI badges represent unit test status and the code coverage
of those unit tests. We require 100% unit test success (Hence the pass / fail)
and that code coverage percentage does not lower.

Supported Versions

|  Host Type         |  Toolchain    |  Status
|  :---------------  |  :----------  |  :--------------------
|  [Windows-Latest]  |  Python 3.10  |  [![ci]][_ci]
|  [Windows-Latest]  |  Python 3.11  |  [![ci]][_ci]
|  [Windows-Latest]  |  Python 3.12  |  [![ci]][_ci]
|  [Ubuntu-Latest]   |  Python 3.10  |  [![ci]][_ci]
|  [Ubuntu-Latest]   |  Python 3.11  |  [![ci]][_ci]
|  [Ubuntu-Latest]   |  Python 3.12  |  [![ci]][_ci]
|  [MacOS-Latest]    |  Python 3.10  |  [![coming_soon]][_ci]
|  [MacOS-Latest]    |  Python 3.11  |  [![coming_soon]][_ci]
|  [MacOS-Latest]    |  Python 3.12  |  [![coming_soon]][_ci]

### Current Release

[![pypi]][_pypi]

All release information is now tracked with Github
 [tags](https://github.com/tianocore/edk2-pytool-library/tags),
 [releases](https://github.com/tianocore/edk2-pytool-library/releases) and
 [milestones](https://github.com/tianocore/edk2-pytool-library/milestones).

## Content

The package contains classes and modules that can be used as the building blocks
of tools that are relevant to UEFI firmware developers.  These modules should
attempt to provide generic support and avoid tightly coupling with specific use
cases.  It is expected these modules do not provide direct interaction with the
user (through command line interfaces) but instead are intended to be wrapped in
other scripts/tools which contains the specific usage and interface.

Examples:

* File parsers for edk2 specific file types.  These parse the file and provide
  an object for interacting with the content.
* UEFI specific services for encoding/decoding binary structures.
* UEFI defined values and interfaces for usage in python
* Python wrappers for other system cli tools ( signtool, catalog file
  generation, inf file generation, etc)
* Python utilities to provide consistent logging, command invocation, path
  resolution, etc

## License

All content in this repository is licensed under [BSD-2-Clause Plus Patent
License](license.txt).

[![PyPI -
License](https://img.shields.io/pypi/l/edk2_pytool_library.svg)](https://pypi.org/project/edk2-pytool-library/)

## Usage

NOTE: It is strongly recommended that you use python virtual environments.
Virtual environments avoid changing the global python workspace and causing
conflicting dependencies.  Virtual environments are lightweight and easy to use.
[Learn more](https://docs.python.org/3/library/venv.html)

* To install run `pip install --upgrade edk2-pytool-library`
* To use in your python code

    ```python
    from edk2toollib.<module> import <class>
    ```

## History

This library and functionality was ported from Project Mu. For history and
documentation prior to this see the original Project Mu project
<https://github.com/microsoft/mu_pip_python_library>

## Contribution Process

This project welcomes all types of contributions. For issues, bugs, and
questions it is best to open a [github
issue](https://github.com/tianocore/edk2-pytool-library/issues).

### Code Contributions

For code contributions this project leverages github pull requests.  See github
tutorials, help, and documentation for complete descriptions. For best success
please follow the below process.

1. Contributor opens an issue describing problem or new desired functionality
2. Contributor forks repository in github
3. Contributor creates branch for work in their fork
4. Contributor makes code changes, writes relevant unit tests, authors
   documentation and release notes as necessary.
5. Contributor runs tests locally
6. Contributor submits PR to master branch of tianocore/edk2-pytool-library
    1. PR reviewers will provide feedback on change.  If any modifications are
       required, contributor will make changes and push updates.
    2. PR automation will run and validate tests pass
    3. If all comments resolved, maintainers approved, and tests pass the PR
       will be squash merged and closed by the maintainers.

## Maintainers

See the [github
team](https://github.com/orgs/tianocore/teams/edk-ii-tool-maintainers) for more
details.

## Documentation

[![docs]][_docs]

### Users and Consumers

Documentation for the most recent release of edk2-pytool-library is hosted on
[tianocore.org/edk2-pytool-library](https://www.tianocore.org/edk2-pytool-library/).
Raw documentation is located in the ```docs/``` folder and is split into two
separate categories. The first is located at ```docs/user/``` and is
documentation and API references for those that are using this package in their
own project. Users can generate a local copy of the documentation by executing the
following command from the root of the project:

```cmd
pip install --upgrade -e .[docs]
mkdocs serve
```

### Contributors

Contributor documentation is located at [docs/contributor/](https://github.com/tianocore/edk2-pytool-library/tree/master/docs/contributor)
 and contains instructions for:

* Setting up a development and testing environment
* How edk2pytools is versioned and published
* How to publish a release
* Contributing to the edk2-pytool-extensions repository

[codecov]: https://codecov.io/gh/tianocore/edk2-pytool-library/branch/master/graph/badge.svg
[_codecov]: https://codecov.io/gh/tianocore/edk2-pytool-extensions/
[pypi]: https://img.shields.io/pypi/v/edk2_pytool_library.svg
[_pypi]: https://pypi.org/project/edk2-pytool-library/
[ci]: https://github.com/tianocore/edk2-pytool-library/actions/workflows/run-ci.yml/badge.svg?branch=master
[_ci]: https://github.com/tianocore/edk2-pytool-library/actions/workflows/run-ci.yml
[Windows-Latest]: https://github.com/actions/runner-images
[Ubuntu-Latest]: https://github.com/actions/runner-images
[MacOS-Latest]: https://github.com/actions/runner-images
[docs]: https://img.shields.io/website?label=docs&url=https%3A%2F%2Fwww.tianocore.org%2Fedk2-pytool-library%2F
[_docs]: https://www.tianocore.org/edk2-pytool-library/
[coming_soon]: https://img.shields.io/badge/CI-coming_soon-blue
