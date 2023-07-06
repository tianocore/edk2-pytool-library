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
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    inf_table = InfTable(n_jobs = 1)

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
    inf_table.parse(db)
    table = db.table("inf")

    assert len(table) == 1
    row = table.all()[0]

    assert row['PATH'] in (empty_tree.ws / lib1).as_posix()
    assert row['LIBRARIES_USED'] == libs
    assert row['PROTOCOLS_USED'] == protocols
    assert row['GUIDS_USED'] == guids
    assert sorted(row['SOURCES_USED']) == sorted(sources + sources_ia32 + sources_x64)
