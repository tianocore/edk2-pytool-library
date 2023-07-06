##
# unittest for the LibraryQuery query
#
# Copyright (c) Microsoft Corporation
#
# Spdx-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Unittest for the LibraryQuery query."""
from common import Tree, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB
from edk2toollib.database.queries import LibraryQuery
from edk2toollib.database.tables import InfTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_simple_library_query(empty_tree: Tree):
    """Tests that libraries are detected."""
    empty_tree.create_library("TestLib1", "TestCls")
    empty_tree.create_library("TestLib2", "TestCls")
    empty_tree.create_library("TestLib3", "TestOtherCls")

    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    db.register(InfTable())
    db.parse()

    result = db.search(LibraryQuery(library = "TestCls"))
    assert len(result) == 2

    result = db.search(LibraryQuery(library = "TestOtherCls"))
    assert len(result) == 1

    result = db.search(LibraryQuery())
    assert len(result) == 3
