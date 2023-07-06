##
# unittests for the InstancedInfTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""unittests for the InfTable generator."""
import logging
from pathlib import Path

import pytest
from common import Tree, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.tables import InstancedInfTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_valid_dsc(empty_tree: Tree):
    """Tests that a typical dsc can be correctly parsed."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    comp1 = empty_tree.create_component("TestComponent1", "DXE_DRIVER")
    lib1 = empty_tree.create_library("TestLib1", "TestCls")
    dsc = empty_tree.create_dsc(
        libraryclasses = [lib1],
        components = [str(empty_tree.ws / comp1), lib1]  # absolute comp path
    )

    inf_table = InstancedInfTable(env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32",
        "TARGET": "DEBUG",
    })
    inf_table.parse(db)

    # Check that only 1 component is picked up, as libraries in the component section are ignored
    assert len(db.table("instanced_inf")) == 1
    entry = db.table("instanced_inf").all()[0]
    assert entry["NAME"] == Path(comp1).stem

def test_no_active_platform(empty_tree: Tree, caplog):
    """Tests that the dsc table returns immediately when no ACTIVE_PLATFORM is defined."""
    caplog.set_level(logging.DEBUG)
    edk2path = Edk2Path(str(empty_tree.ws), [])
    Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    # Test 1: raise error for missing ACTIVE_PLATFORM
    with pytest.raises(KeyError, match = "ACTIVE_PLATFORM"):
        InstancedInfTable(env = {})

    # Test 2: raise error for missing TARGET_ARCH
    with pytest.raises(KeyError, match = "TARGET_ARCH"):
        InstancedInfTable(env = {
            "ACTIVE_PLATFORM": "Test.dsc"
        })

    # Test 3: raise error for missing TARGET
    with pytest.raises(KeyError, match = "TARGET"):
        InstancedInfTable(env = {
            "ACTIVE_PLATFORM": "Test.dsc",
            "TARGET_ARCH": "IA32",
        })

def test_dsc_with_conditional(empty_tree: Tree):
    """Tests that conditionals inside a DSC works as expected."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    empty_tree.create_library("TestLib", "SortLib")
    comp1 = empty_tree.create_component('TestComponent1', 'DXE_DRIVER')

    dsc = empty_tree.create_dsc(
        components = [
            "!if $(TARGET) == \"RELEASE\"",
            f"{comp1}",
            "!endif"
    ])

    inf_table = InstancedInfTable(env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    })

    inf_table.parse(db)

    assert len(db.table("instanced_inf")) == 0

def test_library_override(empty_tree: Tree):
    """Tests that overrides and null library overrides can be parsed as expected."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    lib1 = empty_tree.create_library("TestLib1", "TestCls")
    lib2 = empty_tree.create_library("TestLib2", "TestCls")
    lib3 = empty_tree.create_library("TestLib3", "TestNullCls")

    comp1 = empty_tree.create_component(
        "TestDriver1", "DXE_DRIVER",
        libraryclasses = ["TestCls"]
    )

    dsc = empty_tree.create_dsc(
        libraryclasses = [
            f'TestCls|{lib1}',
        ],
        components = [
            f'{comp1} {{',
            '<LibraryClasses>',
            '!if $(TARGET) == "DEBUG"',
            f'TestCls|{lib2}',
            f'NULL|{lib3}',
            '!endif',
            '}',
        ]
    )

    inf_table = InstancedInfTable(env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    })
    inf_table.parse(db)

    # Ensure the Test Driver is using TestLib2 from the override and the NULL library was added
    for row in db.table("instanced_inf").all():
        if (row["NAME"] == Path(comp1).stem
            and Path(lib2).as_posix() in row["LIBRARIES_USED"]
            and Path(lib3).as_posix() in row["LIBRARIES_USED"]):
            break
    else:
        assert False

def test_scoped_libraries1(empty_tree: Tree):
    """Ensure that the correct libraries in regards to scoping.

    Checks proper usage of:

    1. $(ARCH).$(MODULE)
    2. $(ARCH)
    """
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    lib1 = empty_tree.create_library("TestLib1", "TestCls")
    lib2 = empty_tree.create_library("TestLib2", "TestCls")
    lib3 = empty_tree.create_library("TestLib3", "TestCls")

    comp1 = empty_tree.create_component("TestDriver1", "PEIM", libraryclasses = ["TestCls"])
    comp2 = empty_tree.create_component("TestDriver2", "SEC", libraryclasses = ["TestCls"])
    comp3 = empty_tree.create_component("TestDriver3", "PEIM", libraryclasses = ["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses = [f'TestCls|{lib1}'],
        libraryclasses_ia32 = [f'TestCls|{lib2}'],
        libraryclasses_ia32_peim = [f'TestCls|{lib3}'],
        components = [],
        components_x64 = [comp1],
        components_ia32 = [comp2, comp3]
    )

    inf_table = InstancedInfTable(env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    })
    inf_table.parse(db)

    # For each driver, verify that the the driver number (1, 2, 3) uses the corresponding lib number (1, 2, 3)
    for row in db.table("instanced_inf").all():
        if "COMPONENT" not in row:  # Only care about looking at drivers, which do not have a component
            assert row["NAME"].replace("Driver", "Lib") in row["LIBRARIES_USED"][0]

def test_scoped_libraries2(empty_tree: Tree):
    """Ensure that the correct libraries in regards to scoping.

    Checks proper usage of:

    1. common.$(MODULE)
    2. common
    """
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    lib1 = empty_tree.create_library("TestLib1", "TestCls")
    lib2 = empty_tree.create_library("TestLib2", "TestCls")

    comp1 = empty_tree.create_component("TestDriver1", "PEIM", libraryclasses = ["TestCls"])
    comp2 = empty_tree.create_component("TestDriver2", "SEC", libraryclasses = ["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses_common_peim = [f'TestCls|{lib1}'],
        libraryclasses = [f'TestCls|{lib2}'],
        components = [],
        components_x64 = [comp1, comp2],
    )

    inf_table = InstancedInfTable(env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    })
    inf_table.parse(db)

    for row in db.table("instanced_inf").all():
        if "COMPONENT" not in row:
            assert row["NAME"].replace("Driver", "Lib") in row["LIBRARIES_USED"][0]

def test_missing_library(empty_tree: Tree):
    """Test when a library is missing."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    comp1 = empty_tree.create_component("TestDriver1", "PEIM", libraryclasses = ["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses = [],
        components = [],
        components_x64 = [comp1],
    )

    inf_table = InstancedInfTable(env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    })
    with pytest.raises(RuntimeError):
        inf_table.parse(db)
