## @file setup.py
# This contains setup info for edk2-pytool-library pip module
#
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import setuptools
from setuptools.command.sdist import sdist
from setuptools.command.install import install
from setuptools.command.develop import develop
from edk2toollib.windows.locate_tools import _DownloadVsWhere

with open("readme.md", "r") as fh:
    long_description = fh.read()


class PostSdistCommand(sdist):
    """Post-sdist."""
    def run(self):
        # we need to download vswhere so throw the exception if we don't get it
        _DownloadVsWhere()
        sdist.run(self)


class PostInstallCommand(install):
    """Post-install."""
    def run(self):
        install.run(self)
        _DownloadVsWhere()


class PostDevCommand(develop):
    """Post-develop."""
    def run(self):
        develop.run(self)
        try:
            _DownloadVsWhere()
        except:
            pass


setuptools.setup(
    name="edk2-pytool-library",
    author="Tianocore Edk2-PyTool-Library team",
    author_email="sean.brogan@microsoft.com",
    description="Python library supporting UEFI EDK2 firmware development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tianocore/edk2-pytool-library",
    license='BSD+Patent',
    packages=setuptools.find_packages(),
    cmdclass={
        'sdist': PostSdistCommand,
        'install': PostInstallCommand,
        'develop': PostDevCommand,
    },
    include_package_data=True,
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers"
    ]
)
