##
# unittest for the EnvironmentTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Tests for build an inf file table."""

from datetime import date

from edk2toollib.database import Edk2DB, Environment
from edk2toollib.database.tables import EnvironmentTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_environment_no_version(tmp_path):
    """Test that version is set if not found in the environment variables."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(":memory:", pathobj=edk2path)
    db.register(EnvironmentTable())
    db.parse({})

    with db.session() as session:
        rows = session.query(Environment).all()
        assert len(rows) == 1
        env = rows[0]
        assert env.date.date() == date.today()
        assert env.version == "UNKNOWN"
        assert env.values == []


def test_environment_with_vars(tmp_path):
    """Tests that environment variables are recorded."""
    env = {
        "ACTIVE_PLATFORM": "TestPkg/TestPkg.dsc",
        "TARGET_ARCH": "X64",
        "TOOL_CHAIN_TAG": "VS2019",
        "FLASH_DEFINITION": "TestPkg/TestPkg.fdf",
    }
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(EnvironmentTable())
    db.parse(env)

    with db.session() as session:
        rows = session.query(Environment).all()
        assert len(rows) == 1
        entry = rows[0]
        assert entry.version == "UNKNOWN"
        assert entry.date.date() == date.today()
        assert len(entry.values) == 4

    db.parse(env)

    with db.session() as session:
        rows = session.query(Environment).all()
        assert len(rows) == 2
