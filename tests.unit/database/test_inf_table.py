##
# unittest for the InfTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Tests for build an inf file table."""
from common import Tree, empty_tree  # noqa: F401
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
    db.parse({})

    rows = list(db.connection.cursor().execute("SELECT path, library_class FROM inf"))
    assert len(rows) == 2

    for path, library_class in rows:
        assert path in [lib1, lib2]
        assert library_class == "TestCls"

    for inf in [lib1, lib2]:
        rows = db.connection.execute("SELECT * FROM junction WHERE key1 = ? AND table2 = 'source'", (inf,)).fetchall()
        assert len(rows) == 3
