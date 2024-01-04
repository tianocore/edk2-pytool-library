##
# unittest for the Edk2DB class
#
# Copyright (c) Microsoft Corporation
#
# Spdx-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Unittest for the Edk2DB class."""

import pytest
from common import Tree, empty_tree  # noqa: F401
from edk2toollib.database import Edk2DB, Inf
from edk2toollib.database.tables import InfTable, TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_load_existing_db(empty_tree: Tree):
    """Test that we can create a json database and load it later."""
    empty_tree.create_library("TestLib1", "TestCls")
    edk2path = Edk2Path(str(empty_tree.ws), [])

    db_path = empty_tree.ws / "test.db"
    assert db_path.exists() is False

    db = Edk2DB(db_path, pathobj=edk2path)
    db.register(InfTable(n_jobs = 1))
    db.parse({})
    with db.session() as session:
        rows = session.query(Inf).all()
        assert len(rows) == 1

    assert db_path.exists()

    # Ensure we can load an existing database
    db = Edk2DB(db_path, pathobj=edk2path)
    with db.session() as session:
        rows = session.query(Inf).all()
        assert len(rows) == 1

def test_catch_bad_parser_and_query(empty_tree: Tree):
    """Test that a bad parser will be caught and logged."""
    edk2path = Edk2Path(str(empty_tree.ws), [])

    db_path = empty_tree.ws / "test.db"
    assert db_path.exists() is False

    db = Edk2DB(db_path, pathobj=edk2path)
    parser = TableGenerator()
    db.register(parser)

    with pytest.raises(NotImplementedError):
        db.parse({})

    with pytest.raises(NotImplementedError):
        parser.parse(db.session(), db.pathobj, 0, {})

def test_clear_parsers(empty_tree: Tree):
    """Test that we can clear all parsers. EnvironmentTable should always persist."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db = Edk2DB(empty_tree.ws / "test.db", pathobj=edk2path)
    db.register(TableGenerator())
    assert len(db._parsers) == 1

    db.clear_parsers()
    assert len(db._parsers) == 0

def test_multiple_databases_do_not_interfere(empty_tree: Tree):
    empty_tree.create_library("TestLib1", "TestCls")
    edk2path = Edk2Path(str(empty_tree.ws), [])

    db_path1 = empty_tree.ws / "test1.db"
    db_path2 = empty_tree.ws / "test2.db"

    assert db_path1.exists() is False
    assert db_path2.exists() is False

    db1 = Edk2DB(db_path1, pathobj=edk2path)
    db2 = Edk2DB(db_path2, pathobj=edk2path)

    assert db_path1.exists()
    assert db_path2.exists()

    db1.register(InfTable(n_jobs = 1))
    db1.parse({})

    with db1.session() as session:
        rows = session.query(Inf).all()
        assert len(rows) == 1

    with db2.session() as session:
        rows = session.query(Inf).all()
        assert len(rows) == 0
