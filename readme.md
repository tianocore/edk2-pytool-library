# Tianocore Edk2 PyTool Library (edk2toollib)

This is a Tianocore maintained project consisting of a python library supporting UEFI firmware development.  This package's intent is to provide an easy way to organize and share python code to facilitate reuse across environments, tools, and scripts.  Inclusion of this package and dependency management is best managed using Pip/Pypi.

This is a supplemental package and is not required to be used for edk2 builds.

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

## Release Version History

### Version 0.10.4

* Features:
  * If multiple classes are found (ie when searching for a SettingsManager), it will now pick the one that is deepest in hierarchy from the desired class
  * Updated parsers for DSC, FDF, and DEC
* Bugs:
  * #42 - Fix bug causing incorrect decoding in FMP capsule when called twice
  * #41, #58 - Improve Macro resolution in edk2 parsers
  * #49  - Wincert class had bug in write routine
  * #51 - UEFI Status Code did not support error, warning, info bits and did not safely parse the input.  


### Version 0.10.3

* Features:
  * If multiple classes are found (ie when searching for a SettingsManager), it can now pick the one that is closest to the original module file
  * Unified Azure Pipeline
  * Added Capsule object classes to support decoding and encoding
* Bugs
  * Catch errors when emitting invalid characters to the markdown log handler
  * Processor info is now checked in a case insensitive manner (fixes OpenBSD)

### Version 0.10.2

* Features:
  * Add GuidList object to allow easy file system parsing of edk2 files for complete list of guids
  * Add gitignore syntax parser to allow for common method to ignore files or folders in tools
* Bugs:
  * Junit report format module was not escaping all user supplied strings which could cause invalid xml output

### Version 0.10.1

* Bugs:
  * Added better logging when locate_tools queries vcvarsall and can't find a particular key
  * Fixed bug in RunPythonScript that caused an exception
  * Improved XML output by escaping

### Version 0.10.0

* Features:
  * Change DEC parser
    * More complete parser but is not backward compatible.  Users of DEC parser will need to update.
    * LibraryClass, Protocol, Ppi, and Guid sections now parse each line to a custom object which contains all data fields.

### Version 0.9.2

* Bugs:
  * Change QueryVcVariables so environment variable keys are not case sensitive.  On Windows these are not case sensitive and "Path" is not consistent.

### Version 0.9.1

* Features:
  * Add support for getting WinSdk tools on platforms without VS2017 or newer
  * FindToolInWinSdk in locate_tools.py throws a FileNotFoundException when it cannot find the tool requested, previously it returned None
  * Add support for limiting vswhere to certain versions of visual studio (VS2017 and VS2019 supported)

### Version 0.9.00

Initial release of library with functionality ported from Project Mu.
For history and documentation prior to this see the original Project Mu project
https://github.com/microsoft/mu_pip_python_library

## Current Status

[![PyPI](https://img.shields.io/pypi/v/edk2_pytool_library.svg)](https://pypi.org/project/edk2-pytool-library/)

| Host Type | Toolchain | Branch | Build Status | Test Status | Code Coverage |
| :-------- | :-------- | :---- | :----- | :---- | :--- |
| Linux Ubuntu 1604 | Python 3.7.x | master | [![Build Status](https://dev.azure.com/tianocore/edk2-pytools-library/_apis/build/status/edk2-pytool-library%20-%20PR%20Gate%20-%20Linux)](https://dev.azure.com/tianocore/edk2-pytools-library/_build/latest?definitionId=1) | ![Azure DevOps tests](https://img.shields.io/azure-devops/tests/tianocore/edk2-pytools-library/1.svg) | ![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/tianocore/edk2-pytools-library/1.svg) |
| Windows Server 2019 | Python 3.7.x | master | [![Build Status](https://dev.azure.com/tianocore/edk2-pytools-library/_apis/build/status/Edk2-PyTool-Library%20PR%20build%20-%20Win%20-%20VS2019)](https://dev.azure.com/tianocore/edk2-pytools-library/_build/latest?definitionId=2) | ![Azure DevOps tests](https://img.shields.io/azure-devops/tests/tianocore/edk2-pytools-library/2.svg)| ![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/tianocore/edk2-pytools-library/2.svg) |

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
