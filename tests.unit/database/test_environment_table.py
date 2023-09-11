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

from edk2toollib.database import Edk2DB
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


def test_environment_no_version(tmp_path):
    """Test that version is set if not found in the environment variables."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)

    db.parse({})

    rows = list(db.connection.cursor().execute("SELECT * FROM environment"))

    assert len(rows) == 1
    _, actual_date, actual_version = rows[0]

    assert actual_version == 'UNKNOWN'
    assert actual_date.split(" ")[0] == str(date.today())

    rows = list(db.connection.cursor().execute("SELECT key, value FROM environment_values"))
    assert len(rows) == 0

def test_environment_version(tmp_path):
    """Test that version is detected out of environment variables."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)

    db.parse({})

    rows = list(db.connection.cursor().execute("SELECT * FROM environment"))

    assert len(rows) == 1
    _, actual_date, actual_version = rows[0]

    assert actual_date.split(" ")[0] == str(date.today())
    assert actual_version == 'UNKNOWN'

    rows = list(db.connection.cursor().execute("SELECT key, value FROM environment_values"))
    assert len(rows) == 0


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

    db.parse(env)

    rows = list(db.connection.cursor().execute("SELECT * FROM environment"))

    assert len(rows) == 1
    _, actual_date, actual_version = rows[0]

    assert actual_date.split(" ")[0] == str(date.today())
    assert actual_version == 'UNKNOWN'

    rows = list(db.connection.cursor().execute("SELECT * FROM environment_values"))
    assert len(rows) == 4

    db.parse(env)

    rows = list(db.connection.cursor().execute("SELECT * FROM environment"))

    assert len(rows) == 2
