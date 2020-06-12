# Tianocore Edk2 PyTool Library (edk2toollib)

This is a Tianocore maintained project consisting of a python library supporting UEFI firmware development.  This package's intent is to provide an easy way to organize and share python code to facilitate reuse across environments, tools, and scripts.  Inclusion of this package and dependency management is best managed using Pip/Pypi.

This is a supplemental package and is not required to be used for edk2 builds.

## Current Status

| Host Type | Toolchain | Branch | Build Status | Test Status | Code Coverage |
| :-------- | :-------- | :---- | :----- | :---- | :--- |
| Linux Ubuntu 1804 | Python 3.8.x | master | [![Build Status](https://dev.azure.com/tianocore/edk2-pytools-library/_apis/build/status/edk2-pytool-library%20-%20PR%20Gate%20-%20Linux)](https://dev.azure.com/tianocore/edk2-pytools-library/_build/latest?definitionId=1) | ![Azure DevOps tests](https://img.shields.io/azure-devops/tests/tianocore/edk2-pytools-library/1.svg) | ![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/tianocore/edk2-pytools-library/1.svg) |
| Windows Server 2019 | Python 3.8.x | master | [![Build Status](https://dev.azure.com/tianocore/edk2-pytools-library/_apis/build/status/Edk2-PyTool-Library%20PR%20build%20-%20Win%20-%20VS2019)](https://dev.azure.com/tianocore/edk2-pytools-library/_build/latest?definitionId=2) | ![Azure DevOps tests](https://img.shields.io/azure-devops/tests/tianocore/edk2-pytools-library/2.svg)| ![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/tianocore/edk2-pytools-library/2.svg) |

### Current Release

[![PyPI](https://img.shields.io/pypi/v/edk2_pytool_library.svg)](https://pypi.org/project/edk2-pytool-library/)

All release information is now tracked with Github
 [tags](https://github.com/tianocore/edk2-pytool-library/tags),
  [releases](https://github.com/tianocore/edk2-pytool-library/releases) and
  [milestones](https://github.com/tianocore/edk2-pytool-library/milestones).

## Content

The package contains classes and modules that can be used as the building blocks of tools that are relevant to UEFI firmware developers.  These modules should attempt to provide generic support and avoid tightly coupling with specific use cases.  It is expected these modules do not provide direct interaction with the user (through command line interfaces) but instead are intended to be wrapped in other scripts/tools which contains the specific usage and interface.

Examples:

* File parsers for edk2 specific file types.  These parse the file and provide an object for interacting with the content.
* UEFI specific services for encoding/decoding binary structures.
* UEFI defined values and interfaces for usage in python
* Python wrappers for other system cli tools ( signtool, catalog file generation, inf file generation, etc)
* Python utilities to provide consistent logging, command invocation, path resolution, etc

## License

All content in this repository is licensed under [BSD-2-Clause Plus Patent License](license.txt).

[![PyPI - License](https://img.shields.io/pypi/l/edk2_pytool_library.svg)](https://pypi.org/project/edk2-pytool-library/)

## Usage

NOTE: It is strongly recommended that you use python virtual environments.  Virtual environments avoid changing the global python workspace and causing conflicting dependencies.  Virtual environments are lightweight and easy to use.  [Learn more](https://docs.python.org/3/library/venv.html)

* To install run `pip install --upgrade edk2-pytool-library`
* To use in your python code

    ```python
    from edk2toollib.<module> import <class>
    ```

## History

This library and functionality was ported from Project Mu.
For history and documentation prior to this see the original Project Mu project
https://github.com/microsoft/mu_pip_python_library

## Contribution Process

This project welcomes all types of contributions.
For issues, bugs, and questions it is best to open a [github issue](https://github.com/tianocore/edk2-pytool-library/issues).

### Code Contributions

For code contributions this project leverages github pull requests.  See github tutorials, help, and documentation for complete descriptions.
For best success please follow the below process.

1. Contributor opens an issue describing problem or new desired functionality
2. Contributor forks repository in github
3. Contributor creates branch for work in their fork
4. Contributor makes code changes, writes relevant unit tests, authors documentation and release notes as necessary.
5. Contributor runs tests locally
6. Contributor submits PR to master branch of tianocore/edk2-pytool-library
    1. PR reviewers will provide feedback on change.  If any modifications are required, contributor will make changes and push updates.
    2. PR automation will run and validate tests pass
    3. If all comments resolved, maintainers approved, and tests pass the PR will be squash merged and closed by the maintainers.

## Maintainers

See the [github team](https://github.com/orgs/tianocore/teams/edk-ii-tool-maintainers) for more details.

## Documentation

See the github repo __docs__ folder
