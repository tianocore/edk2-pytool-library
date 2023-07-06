##
# unittest for the Edk2DB class
#
# Copyright (c) Microsoft Corporation
#
# Spdx-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Unittest for the Edk2DB class."""
import logging

import pytest
from common import Tree, correlate_env, empty_tree  # noqa: F401
from edk2toollib.database import AdvancedQuery, Edk2DB, TableGenerator
from edk2toollib.database.queries import LibraryQuery
from edk2toollib.database.tables import InfTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_load_each_db_mode(empty_tree: Tree):
    edk2path = Edk2Path(str(empty_tree.ws), [])
    db_path = empty_tree.ws / "test.db"

    with Edk2DB(Edk2DB.FILE_RW, pathobj=edk2path, db_path=db_path):
        pass

    with Edk2DB(Edk2DB.FILE_RO, db_path=db_path):
        pass

    with Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path):
        pass

    with pytest.raises(ValueError, match = "Unknown Database mode."):
        with Edk2DB(5):
            pass

def test_load_existing_db(empty_tree: Tree):
    """Test that we can create a json database and load it later."""
    empty_tree.create_library("TestLib1", "TestCls")
    edk2path = Edk2Path(str(empty_tree.ws), [])

    db_path = empty_tree.ws / "test.db"
    assert db_path.exists() is False

    with Edk2DB(Edk2DB.FILE_RW, pathobj=edk2path, db_path=db_path) as db:
        db.register(InfTable())
        db.parse(edk2path)
        assert len(db.search(LibraryQuery())) == 1

    assert db_path.exists()

    # Ensure we can load an existing database
    with Edk2DB(Edk2DB.FILE_RW, pathobj=edk2path, db_path=db_path) as db:
        assert len(db.search(LibraryQuery())) == 1

def test_catch_bad_parser_and_query(empty_tree: Tree, caplog):
    """Test that a bad parser will be caught and logged."""
    caplog.set_level(logging.ERROR)
    edk2path = Edk2Path(str(empty_tree.ws), [])

    db_path = empty_tree.ws / "test.db"
    assert db_path.exists() is False

    with Edk2DB(Edk2DB.FILE_RW, pathobj=edk2path, db_path=db_path) as db:
        db.register(TableGenerator()) # Not implemented, will throw an error. Caught and logged.
        db.parse(edk2path)

        with pytest.raises(NotImplementedError):
            db.search(AdvancedQuery()) # Not implemented, will throw an error

    for message in [r.message for r in caplog.records]:
        if "failed." in message:
            break
    else:
        pytest.fail("No error message was logged for a failed parser.")

def test_clear_parsers(empty_tree: Tree):
    """Test that we can clear all parsers."""
    edk2path = Edk2Path(str(empty_tree.ws), [])
    with Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path) as db:
        db.register(TableGenerator())
        assert len(db._parsers) == 1

        db.clear_parsers()
        assert len(db._parsers) == 0
