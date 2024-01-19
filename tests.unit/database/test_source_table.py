##
# unittest for the SourceTable generator
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Tests for building a source file table."""
from common import write_file  # noqa: I001
from edk2toollib.database import Source, Edk2DB
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
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(SourceTable(n_jobs = 1))

    # Verify we detect c and h files
    for file in ["file.c", "file.h", "file.asm", "file.cpp"]:
      write_file(tmp_path / file, SOURCE_LICENSE)

    db.parse({})
    with db.session() as session:
      rows = session.query(Source).all()
      assert len(rows) == 4
      for entry in rows:
        assert entry.license == "BSD-2-Clause-Patent"


def test_source_without_license(tmp_path):
    """Tests that a source without a license is detected."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(SourceTable(n_jobs = 1))

    # Verify we detect c and h files
    for file in ["file.c", "file.h"]:
      write_file(tmp_path / file, SOURCE_NO_LICENSE)

    db.parse({})

    with db.session() as session:
      rows = session.query(Source).all()
      assert len(rows) == 2
      for entry in rows:
        assert entry.license == "Unknown"

def test_invalid_filetype(tmp_path):
    """Tests that a source file that is not of the valid type is skipped."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(SourceTable(n_jobs = 1))

    # Ensure we don't catch a file that isnt a c / h file.
    write_file(tmp_path / "file1.py", SOURCE_LICENSE)
    db.parse({})
    with db.session() as session:
      rows = session.query(Source).all()
      assert len(rows) == 0
