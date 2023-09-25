# @file source_table.py
# A module to Parse all Source files and add them to the database.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to Parse all Source files and add them to the database."""
import logging
import re
import time
from pathlib import Path
from sqlite3 import Cursor

from joblib import Parallel, delayed

from edk2toollib.database.tables.base_table import TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

SOURCE_FILES = ["*.c", "*.h", "*.cpp", "*.asm", "*.s", "*.nasm", "*.masm", "*.rs"]

CREATE_SOURCE_TABLE = '''
CREATE TABLE IF NOT EXISTS source (
    path TEXT UNIQUE,
    license TEXT,
    total_lines INTEGER,
    code_lines INTEGER,
    comment_lines INTEGER,
    blank_lines INTEGER
)
'''

INSERT_SOURCE_ROW = '''
INSERT OR REPLACE INTO source (path, license, total_lines, code_lines, comment_lines, blank_lines)
VALUES (?, ?, ?, ?, ?, ?)
'''


class SourceTable(TableGenerator):
    """A Table Generator that parses all c and h files in the workspace."""
    def __init__(self, *args, **kwargs):
        """Initializes the Source Table Parser.

        Args:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments described below

        Keyword Arguments:
            n_jobs (int): Number of files to run in parallel
        """
        self.n_jobs = kwargs.get("n_jobs", -1)

    def create_tables(self, db_cursor: Cursor) -> None:
        """Create the tables necessary for this parser."""
        db_cursor.execute(CREATE_SOURCE_TABLE)

    def parse(self, db_cursor: Cursor, pathobj: Edk2Path, id: str, env: dict) -> None:
        """Parse the workspace and update the database."""
        ws = Path(pathobj.WorkspacePath)
        self.pathobj = pathobj

        start = time.time()
        files = []
        for src in SOURCE_FILES:
            files.extend(list(ws.rglob(src)))
        files = [file for file in files if not file.is_relative_to(ws / "Build")]
        src_entries = Parallel(n_jobs=self.n_jobs)(delayed(self._parse_file)(ws, filename) for filename in files)
        logging.debug(
            f"{self.__class__.__name__}: Parsed {len(src_entries)} files; "
            f"took {round(time.time() - start, 2)} seconds.")

        db_cursor.executemany(INSERT_SOURCE_ROW, src_entries)

    def _parse_file(self, ws, filename: Path) -> dict:
        """Parse a C file and return the results."""
        license = ""
        with open(filename, 'r', encoding='cp850') as f:
            for line in f.readlines():
                match = re.search(r"SPDX-License-Identifier:\s*(.*)$", line)  # TODO: This is not a standard format.
                if match:
                    license = match.group(1)
        return (
            self.pathobj.GetEdk2RelativePathFromAbsolutePath(filename.as_posix()),  # path
            license or "Unknown",  # license
            0,  # total_lines
            0,  # code_lines
            0,  # comment_lines
            0,  # blank_lines
        )
