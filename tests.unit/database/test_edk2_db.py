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
from edk2toollib.database import Edk2DB
from edk2toollib.database.tables import InfTable
from edk2toollib.database.tables.base_table import TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_load_existing_db(empty_tree: Tree):
    """Test that we can create a json database and load it later."""
    empty_tree.create_library("TestLib1", "TestCls")
    edk2path = Edk2Path(str(empty_tree.ws), [])

    db_path = empty_tree.ws / "test.db"
    assert db_path.exists() is False

    with Edk2DB(db_path, pathobj=edk2path) as db:
        db.register(InfTable(n_jobs = 1))
        db.parse({})
        result = db.connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", ("inf",)).fetchone()
        assert result is not None

    assert db_path.exists()

    # Ensure we can load an existing database
    with Edk2DB(db_path, pathobj=edk2path) as db:
        result = db.connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", ("inf",)).fetchone()
        assert result is not None

def test_catch_bad_parser_and_query(empty_tree: Tree):
    """Test that a bad parser will be caught and logged."""
    edk2path = Edk2Path(str(empty_tree.ws), [])

    db_path = empty_tree.ws / "test.db"
    assert db_path.exists() is False


    with Edk2DB(db_path, pathobj=edk2path) as db:
        parser = TableGenerator()
        db.register(parser)

        with pytest.raises(NotImplementedError):
            db.parse({})

        with pytest.raises(NotImplementedError):
            parser.parse(db.connection.cursor(), db.pathobj, 0, {})

def test_clear_parsers(empty_tree: Tree):
    """Test that we can clear all parsers. EnvironmentTable should always persist."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    with Edk2DB(empty_tree.ws / "test.db", pathobj=edk2path) as db:
        db.register(TableGenerator())
        assert len(db._parsers) == 2

        db.clear_parsers()
        assert len(db._parsers) == 1
