##
# unittest for the InfTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Tests for build an inf file table."""
from pathlib import Path

from common import Tree, empty_tree, write_file  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.tables import InfTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_valid_inf(empty_tree: Tree):
    """Tests that a valid Inf with typical settings is properly parsed."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InfTable(n_jobs = 1))

    # Configure inf
    libs = ["TestLib2", "TestLib3"]
    protocols = ['gEfiTestProtocolGuid']
    guids = ['gEfiTestTokenSpaceGuid']
    sources = ['Test.c']
    sources_ia32 = ['IA32/Test.c']
    sources_x64 = ['X64/Test.c']

    lib1 = empty_tree.create_library(
        "TestLib1", "TestCls",
        libraryclasses = libs,
        protocols = protocols,
        guids = guids,
        sources = sources,
        sources_ia32 = sources_ia32,
        sources_x64 = sources_x64,
    )
    lib2 = empty_tree.create_library(
        "TestLib2", "TestCls",
        libraryclasses = libs,
        protocols = protocols,
        guids = guids,
        sources = sources,
        sources_ia32 = sources_ia32,
        sources_x64 = sources_x64,
    )

    (empty_tree.library_folder / "IA32").mkdir()
    (empty_tree.library_folder / "X64").mkdir()
    for file in sources + sources_ia32 + sources_x64:
        write_file((empty_tree.library_folder / file).resolve(), "FILLER")

    db.parse({})

    rows = list(db.connection.cursor().execute("SELECT path, library_class FROM inf"))
    assert len(rows) == 2

    for path, library_class in rows:
        assert path in [Path(lib1).as_posix(), Path(lib2).as_posix()]
        assert library_class == "TestCls"

    for inf in [Path(lib1).as_posix(), Path(lib2).as_posix()]:
        rows = db.connection.execute("SELECT * FROM junction WHERE key1 = ? AND table2 = 'source'", (inf,)).fetchall()
        assert len(rows) == 3

def test_source_path_with_dot_dot(empty_tree: Tree):
    """Tests that paths with .. are correctly resolved."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "db.db", pathobj=edk2path)
    db.register(InfTable(n_jobs = 1))
    empty_tree.create_library(
        "TestLib", "TestCls",
        sources = [
            "../Test1.c",
            "Test2.c"
        ]
    )
    file1 = empty_tree.package / "Test1.c"
    file1.touch()
    file2 = empty_tree.library_folder / "Test2.c"
    file2.touch()

    db.parse({})

    # Ensure we resolve file1 as ws / Test1.c and file2 as ws / library/ test2.c
    for path, in db.connection.execute("SELECT key2 FROM junction").fetchall():
        assert Path(empty_tree.ws, path) in [file1, file2]
