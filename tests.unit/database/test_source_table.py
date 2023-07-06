##
# unittest for the SourceTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Tests for building a source file table."""
from common import write_file
from edk2toollib.database import Edk2DB
from edk2toollib.database.tables import SourceTable
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

SOURCE_LICENSE = r"""
/** @file
  This is a description of a fake file

  Copyright (c) Corporation
  SPDX-License-Identifier: BSD-2-Clause-Patent
*//
"""

SOURCE_NO_LICENSE = r"""
/** @file
  This is a description of a fake file

  Copyright (c) Corporation
*//
"""


def test_source_with_license(tmp_path):
    """Tests that a source with a license is detected and the license is set."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    source_table = SourceTable(n_jobs = 1)

    # Verify we detect c and h files
    for file in ["file.c", "file.h", "file.asm", "file.cpp"]:
      write_file(tmp_path / file, SOURCE_LICENSE)

      source_table.parse(db)
      table = db.table("source")
      assert len(table) == 1
      row = table.all()[0]
      assert row["PATH"] == (tmp_path / file).relative_to(tmp_path).as_posix()
      assert row["LICENSE"] == "BSD-2-Clause-Patent"

      db.drop_table("source")
      (tmp_path / file).unlink()


    # Ensure we don't catch a file that isnt a c / h file.
    write_file(tmp_path / "file1.py", SOURCE_LICENSE)
    source_table.parse(db)
    table = db.table("source")
    assert len(table) == 0

def test_source_without_license(tmp_path):
    """Tests that a source without a license is detected."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path)
    source_table = SourceTable(n_jobs = 1)


    # Verify we detect c and h files
    for file in ["file.c", "file.h"]:
      write_file(tmp_path / file, SOURCE_NO_LICENSE)

      source_table.parse(db)
      table = db.table("source")
      assert len(table) == 1
      row = table.all()[0]
      assert row["PATH"] == (tmp_path / file).relative_to(tmp_path).as_posix()
      assert row["LICENSE"] == ""

      db.drop_table("source")
      (tmp_path / file).unlink()


    # Ensure we don't catch a file that isnt a c / h file.
    write_file(tmp_path / "file1.py", SOURCE_LICENSE)
    source_table.parse(db)
    table = db.table("source")
    assert len(table) == 0
