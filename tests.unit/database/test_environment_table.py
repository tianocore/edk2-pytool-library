##
# unittest for the EnvironmentTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""Tests for build an inf file table."""
import os
from datetime import date
from edk2toollib.database.tables import EnvironmentTable
from edk2toollib.database import Edk2DB
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

def test_environment_no_version():
    """Test that version is set if not found in the environment variables."""
    edk2path = Edk2Path(os.getcwd(), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    env_table = EnvironmentTable(env={})

    env_table.parse(db)
    table = db.table("environment")

    assert len(table) == 1
    row = table.all()[0]

    assert row['VERSION'] == 'UNKNOWN'
    assert row["DATE"] == str(date.today())
    assert row["ENV"] == {}

def test_environment_version():
    """Test that version is detected out of environment variables."""
    edk2path = Edk2Path(os.getcwd(), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    env = {"VERSION": "abcdef1"}
    env_table = EnvironmentTable(env=env)

    env_table.parse(db)
    table = db.table("environment")

    assert len(table) == 1
    row = table.all()[0]

    assert row['VERSION'] == 'abcdef1'
    assert row["DATE"] == str(date.today())
    assert row["ENV"] == {}


def test_environment_with_vars():
    """Tests that environment variables are recorded."""
    edk2path = Edk2Path(os.getcwd(), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    env = {
        "ACTIVE_PLATFORM": "TestPkg/TestPkg.dsc",
        "TARGET_ARCH": "X64",
        "TOOL_CHAIN_TAG": "VS2019",
        "FLASH_DEFINITION": "TestPkg/TestPkg.fdf",
    }
    env_table = EnvironmentTable(env = env)
    env_table.parse(db)

    assert len(db.table("environment")) == 1
    row = db.table("environment").all()[0]

    assert row['VERSION'] == 'UNKNOWN'
    assert row["DATE"] == str(date.today())
    assert row["ENV"] == env
