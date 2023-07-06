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

from joblib import Parallel, delayed
from tinyrecord import transaction

from edk2toollib.database import Edk2DB, TableGenerator

SOURCE_FILES = ["*.c", "*.h", "*.cpp", "*.asm", "*.s", "*.nasm", "*.masm", "*.rs"]


class SourceTable(TableGenerator):
    """A Table Generator that parses all c and h files in the workspace.

    Generates a table with the following schema:

    ``` py
    table_name = "source"
    |-------------------------------------------------------------------------|
    | PATH | LICENSE | TOTAL_LINES | CODE_LINES | COMMENT_LINES | BLANK_LINES |
    |-------------------------------------------------------------------------|
    ```
    """  # noqa: E501
    def __init__(self, *args, **kwargs):
        """Initializes the Source Table Parser.

        Args:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments described below

        Keyword Arguments:
            n_jobs (int): Number of files to run in parallel
        """
        self.n_jobs = kwargs.get("n_jobs", -1)

    def parse(self, db: Edk2DB) -> None:
        """Parse the workspace and update the database."""
        ws = Path(db.pathobj.WorkspacePath)
        src_table = db.table("source", cache_size=None)

        start = time.time()
        files = []
        for src in SOURCE_FILES:
            files.extend(list(ws.rglob(src)))
        files = [file for file in files if not file.is_relative_to(ws / "Build")]
        src_entries = Parallel(n_jobs=self.n_jobs)(delayed(self._parse_file)(ws, filename) for filename in files)
        logging.debug(
            f"{self.__class__.__name__}: Parsed {len(src_entries)} files; "
            f"took {round(time.time() - start, 2)} seconds.")

        with transaction(src_table) as tr:
            tr.insert_multiple(src_entries)

    def _parse_file(self, ws, filename: Path) -> dict:
        """Parse a C file and return the results."""
        license = ""
        with open(filename, 'r', encoding='cp850') as f:
            for line in f.readlines():
                match = re.search(r"SPDX-License-Identifier:\s*(.*)$", line)  # TODO: This is not a standard format.
                if match:
                    license = match.group(1)

        return {
            "PATH": filename.relative_to(ws).as_posix(),
            "LICENSE": license,
            "TOTAL_LINES": 0,
            "CODE_LINES": 0,
            "COMMENT_LINES": 0,
            "BLANK_LINES": 0,
        }
