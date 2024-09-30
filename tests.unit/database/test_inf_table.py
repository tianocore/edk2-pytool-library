##
# unittest for the InfTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Tests for build an inf file table."""

import shutil
from pathlib import Path

from common import Tree, empty_tree, write_file  # noqa: F401
from edk2toollib.database import Edk2DB, Inf
from edk2toollib.database.tables import InfTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_valid_inf(empty_tree: Tree):
    """Tests that a valid Inf with typical settings is properly parsed."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InfTable(n_jobs=1))

    # Configure inf
    libs = ["TestLib2", "TestLib3"]
    protocols = ["gEfiTestProtocolGuid"]
    guids = ["gEfiTestTokenSpaceGuid"]
    sources = ["Test.c"]
    sources_ia32 = ["IA32/Test.c"]
    sources_x64 = ["X64/Test.c"]

    lib1 = empty_tree.create_library(
        "TestLib1",
        "TestCls",
        libraryclasses=libs,
        protocols=protocols,
        guids=guids,
        sources=sources,
        sources_ia32=sources_ia32,
        sources_x64=sources_x64,
    )
    lib2 = empty_tree.create_library(
        "TestLib2",
        "TestCls",
        libraryclasses=libs,
        protocols=protocols,
        guids=guids,
        sources=sources,
        sources_ia32=sources_ia32,
        sources_x64=sources_x64,
    )

    (empty_tree.library_folder / "IA32").mkdir()
    (empty_tree.library_folder / "X64").mkdir()
    for file in sources + sources_ia32 + sources_x64:
        write_file((empty_tree.library_folder / file).resolve(), "FILLER")

    db.parse({})

    with db.session() as session:
        rows = session.query(Inf).all()
        assert len(rows) == 2
        for row in rows:
            assert row.path in [Path(lib1).as_posix(), Path(lib2).as_posix()]
            assert row.library_class == "TestCls"

        for inf in [Path(lib1).as_posix(), Path(lib2).as_posix()]:
            row = session.query(Inf).filter(Inf.path == inf).first()
            assert len(row.sources) == 3


def test_source_path_with_dot_dot(empty_tree: Tree):
    """Tests that paths with .. are correctly resolved."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InfTable(n_jobs=1))
    empty_tree.create_library("TestLib", "TestCls", sources=["../Test1.c", "Test2.c"])
    file1 = empty_tree.package / "Test1.c"
    file1.touch()
    file2 = empty_tree.library_folder / "Test2.c"
    file2.touch()

    db.parse({})
    with db.session() as session:
        for row in session.query(Inf).all():
            for source in row.sources:
                assert empty_tree.ws / source.path in [file1, file2]


def test_pkg_not_pkg_path_relative(empty_tree: Tree):
    """Tests when a package is not itself relative to a package path.

    !!! example
        pp = ["Common"]
        pkg1 "Common/Package1"
        pkg2 "Common/Packages/Package2"

        assert pkg1.relative == "Package1"
        assert pkg2.relative == "Packges/Package2"
    """
    empty_tree.create_library("TestLib", "TestCls", sources=["Test2.c"])
    file2 = empty_tree.library_folder / "Test2.c"
    file2.touch()

    ws = empty_tree.ws
    common = ws / "Common"

    shutil.copytree(ws, common)
    shutil.rmtree(ws / "TestPkg")

    edk2path = Edk2Path(str(ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InfTable(n_jobs=1))
    db.parse({})

    with db.session() as session:
        inf = session.query(Inf).one()
        assert len(inf.sources) == 1
        assert inf.sources[0].path == Path("Common", "TestPkg", "Library", "Test2.c").as_posix()
        assert inf.path == Path("Common", "TestPkg", "Library", "TestLib.inf").as_posix()
