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
from edk2toollib.database import Edk2DB, InstancedInf, Source
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
        libraryclasses=[lib1],
        components=[str(empty_tree.ws / comp1), lib1],  # absolute comp path
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    with db.session() as session:
        rows = session.query(InstancedInf).all()
        assert len(rows) == 1
        assert rows[0].component == Path(comp1).as_posix()


def test_no_active_platform(empty_tree: Tree, caplog):
    """Tests that the dsc table returns immediately when no ACTIVE_PLATFORM is defined."""
    caplog.set_level(logging.DEBUG)
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    # Test 1: raise error for missing ACTIVE_PLATFORM
    with pytest.raises(KeyError, match="ACTIVE_PLATFORM"):
        db.parse({})

    # Test 2: raise error for missing TARGET_ARCH
    with pytest.raises(KeyError, match="TARGET_ARCH"):
        db.parse({"ACTIVE_PLATFORM": "Test.dsc"})

    # Test 3: raise error for missing TARGET
    with pytest.raises(KeyError, match="TARGET"):
        db.parse(
            {
                "ACTIVE_PLATFORM": "Test.dsc",
                "TARGET_ARCH": "IA32",
            }
        )


def test_dsc_with_conditional(empty_tree: Tree):
    """Tests that conditionals inside a DSC works as expected."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    empty_tree.create_library("TestLib", "SortLib")
    comp1 = empty_tree.create_component("TestComponent1", "DXE_DRIVER")

    dsc = empty_tree.create_dsc(components=['!if $(TARGET) == "RELEASE"', f"{comp1}", "!endif"])

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    with db.session() as session:
        rows = session.query(InstancedInf).all()
        assert len(rows) == 0


def test_library_override(empty_tree: Tree):
    """Tests that overrides and null library overrides can be parsed as expected."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library("TestLib1", "TestCls")
    lib2 = empty_tree.create_library("TestLib2", "TestCls")
    lib3 = empty_tree.create_library("TestLib3", "TestNullCls")

    comp1 = empty_tree.create_component("TestDriver1", "DXE_DRIVER", libraryclasses=["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses=[
            f"TestCls|{lib1}",
        ],
        components=[
            f"{comp1} {{",
            "<LibraryClasses>",
            '!if $(TARGET) == "DEBUG"',
            f"TestCls|{lib2}",
            f"NULL|{lib3}",
            "!endif",
            "}",
        ],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)
    with db.session() as session:
        for entry in session.query(InstancedInf).filter_by(path=Path(comp1).as_posix()).all():
            assert len(entry.libraries) == 2
            for library in entry.libraries:
                assert library.name in ["TestLib2", "TestLib3"]


def test_scoped_libraries1(empty_tree: Tree):
    """Ensure that the correct libraries in regards to scoping.

    Checks proper usage of:

    1. $(ARCH).$(MODULE)
    2. $(ARCH)
    """
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library("TestLib1", "TestCls", sources=["File1.c"])
    lib2 = empty_tree.create_library("TestLib2", "TestCls", sources=["File2.c"])
    lib3 = empty_tree.create_library("TestLib3", "TestCls", sources=["File3.c"])

    comp1 = empty_tree.create_component("TestDriver1", "PEIM", libraryclasses=["TestCls"])
    comp2 = empty_tree.create_component("TestDriver2", "SEC", libraryclasses=["TestCls"])
    comp3 = empty_tree.create_component("TestDriver3", "PEIM", libraryclasses=["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses=[f"TestCls|{lib1}"],
        libraryclasses_ia32=[f"TestCls|{lib2}"],
        libraryclasses_ia32_peim=[f"TestCls|{lib3}"],
        components=[],
        components_x64=[comp1],
        components_ia32=[comp2, comp3],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    with db.session() as session:
        for component in session.query(InstancedInf).filter_by(cls=None).all():
            assert len(component.libraries) == 1
            component_path = Path(component.path)
            library_path = Path(component.libraries[0].path)
            assert library_path.name == component_path.name.replace("Driver", "Lib")

        source_list = session.query(Source).all()
        assert len(source_list) == 3
        for source in source_list:
            assert Path(source.path).name in ["File1.c", "File2.c", "File3.c"]


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

    comp1 = empty_tree.create_component("TestDriver1", "PEIM", libraryclasses=["TestCls"])
    comp2 = empty_tree.create_component("TestDriver2", "SEC", libraryclasses=["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses_common_peim=[f"TestCls|{lib1}"],
        libraryclasses=[f"TestCls|{lib2}"],
        components=[],
        components_x64=[comp1, comp2],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)

    with db.session() as session:
        for component in session.query(InstancedInf).filter_by(cls=None).all():
            assert len(component.libraries) == 1
            component_path = Path(component.path)
            library_path = Path(component.libraries[0].path)
            assert library_path.name == component_path.name.replace("Driver", "Lib")


def test_missing_library(empty_tree: Tree):
    """Test when a library is missing."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    comp1 = empty_tree.create_component("TestDriver1", "PEIM", libraryclasses=["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses=[],
        components=[],
        components_x64=[comp1],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32 X64",
        "TARGET": "DEBUG",
    }
    db.parse(env)
    with db.session() as session:
        component = session.query(InstancedInf).filter_by(cls=None).one()
        assert len(component.libraries) == 0
    # key2 = db.connection.execute("SELECT instanced_inf2 FROM instanced_inf_junction").fetchone()[0]
    # assert key2 is None  # This library class does not have an instance available, so key2 should be None


def test_multiple_library_class(empty_tree: Tree):
    """Test that a library INF that has multiple library class definitions is handled correctly."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(":memory:", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library(
        "TestLib",
        "TestCls",
        default={
            "MODULE_TYPE": "BASE",
            "BASE_NAME": "TestLib1",
            "LIBRARY_CLASS 1": "TestCls1",
            "LIBRARY_CLASS 2": "TestCls2",
        },
    )

    comp1 = empty_tree.create_component("TestDriver1", "DXE_RUNTIME_DRIVER", libraryclasses=["TestCls1"])
    comp2 = empty_tree.create_component("TestDriver2", "DXE_DRIVER", libraryclasses=["TestCls2"])

    dsc = empty_tree.create_dsc(
        libraryclasses=[f"TestCls1|{lib1}", f"TestCls2|{lib1}"],
        components=[comp1, comp2],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "X64",
        "TARGET": "DEBUG",
    }

    db.parse(env)

    with db.session() as session:
        infs = session.query(InstancedInf).filter_by(cls=None).all()
        assert len(infs) == 2

        assert infs[0].path == Path(comp1).as_posix()  # If this fails, The order of returned objects may have changed
        assert len(infs[0].libraries) == 1
        assert infs[0].libraries[0].path == Path(lib1).as_posix()
        assert infs[0].libraries[0].cls == "TestCls1"

        assert infs[1].path == Path(comp2).as_posix()  # If this fails, The order of returned objects may have changed
        assert len(infs[1].libraries) == 1
        assert infs[1].libraries[0].path == Path(lib1).as_posix()
        assert infs[1].libraries[0].cls == "TestCls2"


def test_absolute_paths_in_dsc(empty_tree: Tree):
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library("TestLib", "TestCls")
    comp1 = empty_tree.create_component("TestDriver", "DXE_DRIVER", libraryclasses=["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses=[
            f"TestCls| {str(empty_tree.ws / lib1)}",
        ],
        components=[
            str(empty_tree.ws / comp1),
        ],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "X64",
        "TARGET": "DEBUG",
    }

    db.parse(env)

    with db.session() as session:
        rows = session.query(InstancedInf).all()
        assert len(rows) == 2
        assert rows[0].path == Path(lib1).as_posix()
        assert rows[1].path == Path(comp1).as_posix()


def test_closest_packagepath(empty_tree: Tree):
    common_folder = empty_tree.ws / "Common"
    common_folder.mkdir()
    sub_folder = common_folder / "SubFolder"
    sub_folder.mkdir()

    (sub_folder / "Library").mkdir()
    (sub_folder / "Drivers").mkdir()

    empty_tree.create_library("TestLib", "TestCls")
    empty_tree.create_component("TestDriver", "DXE_DRIVER", libraryclasses=["TestCls"])

    # Move the files into our subfolder that has two levels of package paths
    (empty_tree.library_folder / "TestLib.inf").rename(sub_folder / "Library" / "TestLib.inf")
    (empty_tree.component_folder / "TestDriver.inf").rename(sub_folder / "Drivers" / "TestDriver.inf")

    # Specify the file paths to be relative to the farther away package path
    dsc = empty_tree.create_dsc(
        libraryclasses=[
            "TestCls|SubFolder/Library/TestLib.inf",
        ],
        components=[
            "SubFolder/Drivers/TestDriver.inf",
        ],
    )

    edk2path = Edk2Path(str(empty_tree.ws), ["Common", "Common/SubFolder"])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "X64",
        "TARGET": "DEBUG",
    }

    db.parse(env)

    with db.session() as session:
        rows = session.query(InstancedInf).all()
        for row in rows:
            assert row.path.startswith(("Library", "Drivers"))


def test_dsc_with_component_section_moduletype_definition(empty_tree: Tree, caplog):
    """Component sections with a moduletype definition is not necessary and should be ignored.

    Per the DSC specification, this is not supported, but the DSC parser just ignores it.
    [Components.IA32.DXE_DRIVER] -> [Components.IA32]
    This is because the Component INF describes it's own module type.
    """
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library("TestLib", "TestCls")
    comp1 = empty_tree.create_component("TestDriver", "PEIM", libraryclasses=["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses=[
            f"TestCls| {Path(lib1).as_posix()}",
        ],
        components=[],
        components_ia32_PEIM=[
            Path(comp1).as_posix(),
        ],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32",
        "TARGET": "DEBUG",
    }

    # Should not error
    db.parse(env)


def test_dsc_with_null_lib_in_libraryclasses_section(empty_tree: Tree):
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InstancedInfTable())

    lib1 = empty_tree.create_library("TestLib", "TestCls")
    nulllib1 = empty_tree.create_library("NullLib1", "NULL")
    nulllib2 = empty_tree.create_library("NullLib2", "NULL")
    nulllib3 = empty_tree.create_library("NullLib3", "NULL")

    comp1 = empty_tree.create_component("TestDriver", "PEIM", libraryclasses=["TestCls"])

    dsc = empty_tree.create_dsc(
        libraryclasses=[
            f"TestCls| {Path(lib1).as_posix()}",
            f"NULL| {Path(nulllib1).as_posix()}",
        ],
        libraryclasses_x64=[
            f"NULL| {Path(nulllib2).as_posix()}",
        ],
        libraryclasses_x64_DXE_DRIVER=[
            f"NULL| {Path(nulllib3).as_posix()}",
        ],
        components=[],
        components_ia32_PEIM=[
            Path(comp1).as_posix(),
        ],
        components_x64=[
            Path(comp1).as_posix(),
        ],
    )

    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "IA32",
        "TARGET": "DEBUG",
    }

    db.parse(env)

    with db.session() as session:
        component = session.query(InstancedInf).filter_by(cls=None).one()
        assert len(component.libraries) == 2

    db = Edk2DB(":memory:", pathobj=edk2path)
    db.register(InstancedInfTable())
    env = {
        "ACTIVE_PLATFORM": dsc,
        "TARGET_ARCH": "X64",
        "TARGET": "DEBUG",
    }

    db.parse(env)

    with db.session() as session:
        component = session.query(InstancedInf).filter_by(cls=None).one()
        assert len(component.libraries) == 3
