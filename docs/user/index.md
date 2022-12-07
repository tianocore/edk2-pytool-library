# Our Philosophy

Edk2 Pytool Library (edk2toollib) is a Tianocore maintained project consisting
of a python library supporting UEFI firmware development. This package's intent
is to provide an easy way to organize and share python code to facilitate reuse
across environments, tools, and scripts. Inclusion of this package and
dependency management is best managed using Pip/Pypi.

## Content

The package contains classes and modules that can be used as the building
blocks of tools that are relevant to UEFI firmware developers. These modules
should attempt to provide generic support and avoid tightly coupling with
specific use cases. It is expected these modules do not provide direct
interaction with the user (through command line interfaces) but instead are
intended to be wrapped in other scripts/tools which contains the specific usage
 and interface.

Examples:

* File parsers for edk2 specific file types. These parse the file and provide
  an object for interacting with the content.
* UEFI specific services for encoding/decoding binary structures.
* UEFI defined values and interfaces for usage in python
* Python wrappers for other system cli tools ( signtool, catalog file
  generation, inf file generation, etc)
* Python utilities to provide consistent logging, command invocation, path
  resolution, etc

## Getting Started

It is strongly recommended that you use python virtual environments. Virtual
environments avoid changing the global python workspace and causing
conflicting dependencies. Virtual environments are lightweight and easy to use.
[Learn more](https://docs.python.org/3/library/venv.html)

* To install run `pip install --upgrade edk2-pytool-library`
* To use in your python code

    ```python
    from edk2toollib.<module> import <class>
    ```
