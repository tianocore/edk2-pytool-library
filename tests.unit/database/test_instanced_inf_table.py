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

GET_USED_LIBRARIES_QUERY = """
SELECT ii.path
FROM instanced_inf AS ii
JOIN instanced_inf_junction AS iij
ON ii.path = iij.instanced_inf2
WHERE
    iij.component = ?
    AND ii.arch = ?
"""

def test_valid_dsc(empty_tree: Tree):
    """Tests that a typical dsc can be correctly parsed."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    comp1 = empty_tree.create_component("TestComponent1", "DXE_DRIVER")
    lib1 = empty_tree.create_library("TestLib1", "TestCls")
    dsc = empty_tree.create_dsc(
        libraryclasses = [lib1],
        components = [str(empty_tree.ws / comp1), lib1]  # absolute comp path
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    rows = db.connection.cursor().execute("SELECT * FROM instanced_inf").fetchall()
    assert len(rows) == 1
    assert rows[0][3] == Path(comp1).stem

def test_no_active_platform(empty_tree: Tree, caplog):
    """Tests that the dsc table returns immediately when no ACTIVE_PLATFORM is defined."""
    caplog.set_level(logging.DEBUG)
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    # Test 1: raise error for missing ACTIVE_PLATFORM
    with pytest.raises(KeyError, match = "ACTIVE_PLATFORM"):
        db.parse({})

    # Test 2: raise error for missing TARGET_ARCH
    with pytest.raises(KeyError, match = "TARGET_ARCH"):
        db.parse({
            "ACTIVE_PLATFORM": "Test.dsc"
        })

    # Test 3: raise error for missing TARGET
    with pytest.raises(KeyError, match = "TARGET"):
        db.parse({
            "ACTIVE_PLATFORM": "Test.dsc",
            "TARGET_ARCH": "IA32",
        })

def test_dsc_with_conditional(empty_tree: Tree):
    """Tests that conditionals inside a DSC works as expected."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    empty_tree.create_library("TestLib", "SortLib")
    comp1 = empty_tree.create_component('TestComponent1', 'DXE_DRIVER')

    dsc = empty_tree.create_dsc(
        components = [
            "!if $(TARGET) == \"RELEASE\"",
            f"{comp1}",
            "!endif"
    ])

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    assert db.connection.cursor().execute("SELECT * FROM instanced_inf").fetchall() == []

def test_library_override(empty_tree: Tree):
    """Tests that overrides and null library overrides can be parsed as expected."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

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

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)
    db.connection.execute("SELECT * FROM junction").fetchall()
    library_list = db.connection.cursor().execute(f"SELECT instanced_inf2 FROM instanced_inf_junction WHERE instanced_inf1 = '{Path(comp1).as_posix()}'").fetchall()

    for path, in library_list:
        assert path in [Path(lib2).as_posix(), Path(lib3).as_posix()]

def test_scoped_libraries1(empty_tree: Tree):
    """Ensure that the correct libraries in regards to scoping.

    Checks proper usage of:

    1. $(ARCH).$(MODULE)
    2. $(ARCH)
    """
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library("TestLib1", "TestCls", sources = ["File1.c"])
    lib2 = empty_tree.create_library("TestLib2", "TestCls", sources = ["File2.c"])
    lib3 = empty_tree.create_library("TestLib3", "TestCls", sources = ["File3.c"])

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

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    for arch in ["IA32", "X64"]:
        for component, in db.connection.execute("SELECT path FROM instanced_inf WHERE component = path and arch is ?;", (arch,)):
            component_lib = db.connection.execute(GET_USED_LIBRARIES_QUERY, (component, arch)).fetchone()[0]
            assert Path(component).name.replace("Driver", "Lib") == Path(component_lib).name

    results = db.connection.execute('SELECT source FROM instanced_inf_source_junction').fetchall()
    assert len(results) == 3
    for source, in results:
        assert Path(source).name in ["File1.c", "File2.c", "File3.c"]

def test_scoped_libraries2(empty_tree: Tree):
    """Ensure that the correct libraries in regards to scoping.

    Checks proper usage of:

    1. common.$(MODULE)
    2. common
    """
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

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

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    for arch in ["IA32", "X64"]:
        for component, in db.connection.execute("SELECT path FROM instanced_inf WHERE component = path and arch is ?;", (arch,)):
            component_lib = db.connection.execute(GET_USED_LIBRARIES_QUERY, (component, arch)).fetchone()[0]
            assert Path(component).name.replace("Driver", "Lib") == Path(component_lib).name

def test_missing_library(empty_tree: Tree):
    """Test when a library is missing."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    comp1 = empty_tree.create_component("TestDriver1", "PEIM", libraryclasses = ["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses = [],
        components = [],
        components_x64 = [comp1],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)
    key2 = db.connection.execute("SELECT instanced_inf2 FROM instanced_inf_junction").fetchone()[0]
    assert key2 is None  # This library class does not have an instance available, so key2 should be None

def test_multiple_library_class(empty_tree: Tree):
    """Test that a library INF that has multiple library class definitions is handled correctly."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library("TestLib", "TestCls", default = {
        "MODULE_TYPE": "BASE",
        "BASE_NAME": "TestLib1",
        "LIBRARY_CLASS 1": "TestCls1",
        "LIBRARY_CLASS 2": "TestCls2",
    })

    comp1 = empty_tree.create_component("TestDriver1", "DXE_RUNTIME_DRIVER", libraryclasses = ["TestCls1"])
    comp2 = empty_tree.create_component("TestDriver2", "DXE_DRIVER", libraryclasses = ["TestCls2"])

    dsc = empty_tree.create_dsc(
        libraryclasses = [
            f'TestCls1|{lib1}',
            f'TestCls2|{lib1}'
        ],
        components = [comp1, comp2],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "X64",
        "TARGET": "DEBUG",
    }

    db.parse(env)

    results = db.connection.execute("SELECT component, instanced_inf1, instanced_inf2 FROM instanced_inf_junction").fetchall()

    # Verify that TestDriver1 uses TestLib acting as TestCls1
    assert results[0] == (Path(comp1).as_posix(), Path(comp1).as_posix(), Path(lib1).as_posix()) # idx 2 is TestDriver1, idx1 is TestLib1 acting as TestCsl1
    assert ("TestLib", "TestCls1") == db.connection.execute(
        "SELECT name, class FROM instanced_inf where path = ? AND component = ?",
        (Path(lib1).as_posix(), Path(comp1).as_posix())).fetchone()

    # Verify that TestDriver2 uses TestLib acting as TestCls2
    assert results[1] == (Path(comp2).as_posix(), Path(comp2).as_posix(), Path(lib1).as_posix())  # idx 4 is TestDriver2, idx 3 is TestLib1 acting as TestCls2
    assert ("TestLib", "TestCls2") == db.connection.execute(
        "SELECT name, class FROM instanced_inf where path = ? AND component = ?",
        (Path(lib1).as_posix(), Path(comp2).as_posix())).fetchone()

def test_absolute_paths_in_dsc(empty_tree: Tree):
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library("TestLib", "TestCls")
    comp1 = empty_tree.create_component("TestDriver", "DXE_DRIVER", libraryclasses=["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses = [
            f'TestCls| {str(empty_tree.ws / lib1)}',
        ],
        components = [
            str(empty_tree.ws / comp1),
        ],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "X64",
        "TARGET": "DEBUG",
    }

    db.parse(env)

    results = db.connection.execute("SELECT path FROM instanced_inf").fetchall()
    assert results[0] == (Path(lib1).as_posix(),)
    assert results[1] == (Path(comp1).as_posix(),)
