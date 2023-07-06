##
# unittest for the UnusedComponentQuery query
#
# Copyright (c) Microsoft Corporation
#
# Spdx-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Unittest for the ComponentQuery query."""
from pathlib import Path

from common import Tree, correlate_env, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.queries import UnusedComponentQuery
from edk2toollib.database.tables import EnvironmentTable, InstancedFvTable, InstancedInfTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_simple_unused_component(empty_tree: Tree):
    """Tests that unused components are detected."""
    lib1 = empty_tree.create_library("TestLib1", "TestCls1")
    lib2 = empty_tree.create_library("TestLib2", "TestCls2")
    empty_tree.create_library("TestLib3", "TestCls3")

    comp1 = empty_tree.create_component(
        "TestDriver1", "DXE_DRIVER",
        libraryclasses = ["TestCls1"]
    )
    comp2 = empty_tree.create_component(
        "TestDriver2", "DXE_DRIVER",
        libraryclasses = ["TestCls2"]
    )

    dsc = empty_tree.create_dsc(
        libraryclasses = [
            f'TestCls1|{lib1}',
            f'TestCls2|{lib2}',
        ],
        components = [
            comp1,
            comp2,
        ]
    )

    fdf = empty_tree.create_fdf(
        fv_testfv = [
            f"INF  {comp1}"
        ]
    )

    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.register(InstancedFvTable(env=env), InstancedInfTable(env=env))
    db.parse()
    comps, libs = db.search(UnusedComponentQuery())

    assert len(comps) == 1 and comps[0] == Path(comp2).as_posix()
    assert len(libs) == 1 and libs[0] == Path(lib2).as_posix()

def test_env_unused_component(empty_tree: Tree):
    """Tests that unused components are detected for different runs."""
    lib1 = empty_tree.create_library("TestLib1", "TestCls")
    lib2 = empty_tree.create_library("TestLib2", "TestCls")
    lib3 = empty_tree.create_library("TestLib3", "TestCls2")
    lib4 = empty_tree.create_library("TestLib4", "TestCls2")

    comp1 = empty_tree.create_component(
        "TestDriver1", "DXE_DRIVER",
        libraryclasses = ["TestCls"]
    )
    comp2 = empty_tree.create_component(
        "TestDriver2", "DXE_DRIVER",
        libraryclasses = ["TestCls2"]
    )

    dsc = empty_tree.create_dsc(
        libraryclasses_ia32 = [
            f'TestCls|{lib1}',
            f'TestCls2|{lib3}',
        ],
        libraryclasses_x64 = [
            f'TestCls|{lib2}',
            f'TestCls2|{lib4}',
        ],
        components = [
            comp1,
            comp2,
        ]
    )

    fdf = empty_tree.create_fdf(
        fv_testfv = [
            f"INF  {comp1}"
        ]
    )

    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)

    env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "IA32",
        "TARGET": "DEBUG",
    }
    db.register(
        InstancedFvTable(env=env),
        InstancedInfTable(env=env),
        EnvironmentTable(env=env),
    )
    db.parse()
    correlate_env(db)

    db.clear_parsers()
    env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "X64",
        "TARGET": "DEBUG",
    }
    db.register(
        InstancedFvTable(env=env),
        InstancedInfTable(env=env),
        EnvironmentTable(env=env),
    )
    db.parse(append=True)
    correlate_env(db)

    # Driver 2 goes unused as it's not in the FDF
    # Driver 2 is built with Lib3 as our first scan is for ARCH IA32
    comps, libs = db.search(UnusedComponentQuery(env_id = 0))
    assert len(comps) == 1 and comps[0] == Path(comp2).as_posix()
    assert len(libs) == 1 and libs[0] == Path(lib3).as_posix()

    # Driver 2 goes unused as it's not in the FDF
    # Driver 2 is built with Lib2 as our second scan is for ARCH X64
    comps, libs = db.search(UnusedComponentQuery(env_id = 1))
    assert len(comps) == 1 and comps[0] == Path(comp2).as_posix()
    assert len(libs) == 1 and libs[0] == Path(lib4).as_posix()

    # Driver 2 goes unused twice (It is built for IA32 and X64) as it's not in the FDF
    # Driver 2 uses Lib3 for once instance, and Lib4 for the other, so both are considered unused
    comps, libs = db.search(UnusedComponentQuery())
    assert len(comps) == 1 and comps[0] == Path(comp2).as_posix()
    assert len(libs) == 2 and sorted(libs) == sorted([Path(lib3).as_posix(), Path(lib4).as_posix()])

def test_ignore_uefi_application(empty_tree: Tree):
    """Tests that UEFI_APPLICATION components are ignored."""
    lib1 = empty_tree.create_library("TestLib1", "TestCls1")

    comp1 = empty_tree.create_component(
        "TestDriver1", "UEFI_APPLICATION",
        libraryclasses = ["TestCls1"]
    )

    dsc = empty_tree.create_dsc(
        libraryclasses = [
            f'TestCls1|{lib1}',
        ],
        components = [
            comp1,
        ]
    )

    fdf = empty_tree.create_fdf(
        fv_testfv = []
    )

    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    env = {
        "ACTIVE_PLATFORM": dsc,
        "FLASH_DEFINITION": fdf,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.register(InstancedFvTable(env=env), InstancedInfTable(env=env))
    db.parse(env)
    comps, libs = db.search(UnusedComponentQuery())

    assert len(comps) == 1 and comps[0] == Path(comp1).as_posix()
    assert len(libs) == 1 and libs[0] == Path(lib1).as_posix()

    comps, libs = db.search(UnusedComponentQuery(ignore_app = True))
    assert len(comps) == 0
    assert len(libs) == 0
