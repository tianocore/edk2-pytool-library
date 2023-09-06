##
# common functions for testing tables
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Common functionality to test the tables."""
import uuid
from pathlib import Path

import pytest
from edk2toollib.database import Edk2DB, Query, transaction
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def correlate_env(db: Edk2DB):
    """Correlates the environment table with the other tables."""
    idx = len(db.table("environment")) - 1
    for table in filter(lambda table: table != "environment", db.tables()):
        table = db.table(table)

        with transaction(table) as tr:
            tr.update({'ENVIRONMENT_ID': idx}, ~Query().ENVIRONMENT_ID.exists())

def write_file(file, contents):
    """Writes contents to a file."""
    file.write_text(contents)
    assert file.read_text() == contents

def make_edk2_cfg_file(*args, **kwargs)->str:
    """Returns a string representing the INF generated.

    Examples:
    ``` python
    inf = make_edk2_cfg_file(defines = {"MODULE_TYPE": "DXE_DRIVER"}, sources = ["CoreCode.h", "CoreCode.c"])
    fdf = make_edk2_cfg_file(fv_testfv = [
      "INF Package/Lib.inf",
      "INF Package/Lib2.inf",
    ])
    ```
    """
    out = ""
    out += "[Defines]\n"

    for key, value in kwargs["defines"].items():  # Must exist
        out += f'  {key} = {value}\n'

    for key, values in kwargs.items():
        if key == "defines":
            continue

        key = key.replace("_", ".")

        out += f"[{key.capitalize()}]\n"
        for value in values:
            # value = value.replace("-", " ")
            out += f'  {value}\n'

    return out

def create_fdf_file(file_path, **kwargs):
    """Makes a FDF with default values that can be overwritten via kwargs."""
    # Make default values.
    defines = {}
    fv_testfv = [
        "INF TestPkg/Components/TestComp.inf",
    ]

    # Override default fv if provided
    k = {
        "defines": kwargs.get("defines", defines),
        "fv_testfv": kwargs.get("fv_testfv", fv_testfv),
    }

    # Append any extra FVs if provided
    for key, value in kwargs.items():
        if key == "defines" or key == "fv_testfv":
            continue

        if key.startswith("fv_"):
            k[key] = value

    # Write to the specified file and return the dict of set values for comparing.
    out = make_edk2_cfg_file(**k)
    write_file(file_path, out)
    return k

def create_dsc_file(file_path, **kwargs):
    """Makes a DSC with default values that can be overwritten via kwargs."""
    # Make default values.
    defines = {}
    libs = ["TestLib|TestPkg/Library/TestLibNull.inf"]
    comps = ["TestPkg/Drivers/TestDriver.inf"]

    # Override default values if they exist
    k = {
        "defines": kwargs.pop("defines", defines),
        "libraryclasses": kwargs.pop("libraryclasses", libs),
        "components": kwargs.pop("components", comps),
    }

    for key,value in kwargs.items():
        k[key] = value

    # Write to the specified file and return the dict of set values For comparing
    out = make_edk2_cfg_file(**k)
    write_file(file_path, out)
    return k

def create_inf_file(file_path, **kwargs):
    """Makes an INF with default values that can be overwritten via kwargs."""
    # Ensure that these sections are always defined, even if empty
    k = {
        "defines": [],
        "sources": [],
        "packages": [],
        "protocols": [],
        "pcd": [],
        "guids": [],
        "libraryclasses": [],
        "depex": [],
    }

    # Merge the two dictionaries (priority given to kwargs)
    ret = {**k, **kwargs}

    # Write to the specified file and return the dict of set values
    # For comparing
    out = make_edk2_cfg_file(**ret)
    write_file(file_path, out)
    return k

class Tree:
    """An empty EDK2 Workspace containing a simple package."""
    def __init__(self, ws: Path):
        """Initializes the empty tree with a package, driver, and library folder."""
        self.ws = ws
        self.edk2path = Edk2Path(str(ws), [])

        self.package = ws / "TestPkg"
        self.package.mkdir()

        dec = self.package / "TestPkg.dec"
        dec.touch()

        self.component_folder = self.package / "Driver"
        self.component_folder.mkdir()

        self.library_folder = self.package / "Library"
        self.library_folder.mkdir()

        self.library_list = []
        self.component_list = []

    def create_library(self, name: str, lib_cls: str, **kwargs):
        """Creates a Library INF in the empty tree."""
        path = self.library_folder / f'{name}.inf'
        default = {
            "FILE_GUID": str(uuid.uuid4()),
            "MODULE_TYPE": "BASE",
            "BASE_NAME": name,
            "LIBRARY_CLASS": lib_cls,
        }
        kwargs["defines"] = {**default, **kwargs.get("defines", {})}
        create_inf_file(path, **kwargs)
        self.library_list.append(str(path))
        return str(path.relative_to(self.ws))

    def create_component(self, name: str, module_type: str, **kwargs):
        """Creates a Component INF in the empty tree."""
        path = self.component_folder / f'{name}.inf'
        kwargs["defines"] = {
            "FILE_GUID": str(uuid.uuid4()),
            "MODULE_TYPE": module_type,
            "BASE_NAME": name,
        }
        create_inf_file(path, **kwargs)
        self.component_list.append(str(path))
        return str(path.relative_to(self.ws))

    def create_dsc(self, **kwargs):
        """Creates a dsc in the empty tree."""
        path = self.package / 'TestPkg.dsc'
        create_dsc_file(path, **kwargs)
        return str(path.relative_to(self.ws))

    def create_fdf(self, **kwargs):
        """Creates an FDF in the Empty Tree."""
        path = self.package / 'TestPkg.fdf'
        create_fdf_file(path, **kwargs)
        return str(path.relative_to(self.ws))





@pytest.fixture
def empty_tree(tmp_path):
    """A Fixture that returns an Tree object."""
    return Tree(tmp_path)
