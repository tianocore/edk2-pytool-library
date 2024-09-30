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

SOURCE_WITH_CODE = r"""
  x = 5
  y = 6
  z = x + y
  print(z)
"""


def test_source_with_license(tmp_path):
    """Tests that a source with a license is detected and the license is set."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(SourceTable(n_jobs=1))

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
    db.register(SourceTable(n_jobs=1))

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
    db.register(SourceTable(n_jobs=1))

    # Ensure we don't catch a file that isnt a c / h file.
    write_file(tmp_path / "file1.py", SOURCE_LICENSE)
    db.parse({})
    with db.session() as session:
        rows = session.query(Source).all()
        assert len(rows) == 0


def test_source_with_code(tmp_path):
    """Tests that a source with code is detected."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(SourceTable(n_jobs=1, source_stats=True, source_extensions=["*.py"]))

    # Verify we detect c and h files
    write_file(tmp_path / "file.py", SOURCE_WITH_CODE)

    db.parse({})

    with db.session() as session:
        file = session.query(Source).one()
        assert file.code_lines == 4


def test_source_with_code_is_updated(tmp_path):
    """Tests that a source with code is updated When parsed again with different source_stats setting."""
    edk2path = Edk2Path(str(tmp_path), [])
    db = Edk2DB(tmp_path / "db.db", pathobj=edk2path)
    db.register(SourceTable(n_jobs=1, source_stats=False, source_extensions=["*.py"]))

    # Verify we detect c and h files
    write_file(tmp_path / "file.py", SOURCE_WITH_CODE)

    db.parse({})

    with db.session() as session:
        file = session.query(Source).one()
        assert (
            file.code_lines == file.total_lines == 5
        )  # When not parsing source_stats, code lines is equal to total lines

    db.clear_parsers()
    db.register(SourceTable(n_jobs=1, source_stats=True, source_extensions=["*.py"]))

    db.parse({})
    with db.session() as session:
        file = session.query(Source).one()
        assert file.code_lines == 4
