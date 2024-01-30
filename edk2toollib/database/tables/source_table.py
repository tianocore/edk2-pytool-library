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
from typing import Any

from joblib import Parallel, delayed
from pygount import SourceAnalysis

from edk2toollib.database import Session, Source
from edk2toollib.database.tables import TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

SOURCE_EXT_LIST = ["*.c", "*.h", "*.cpp", "*.asm", "*.s", "*.nasm", "*.masm", "*.rs"]


class SourceTable(TableGenerator):
    """A Table Generator that parses all c and h files in the workspace."""
    def __init__(self, *args: Any, **kwargs: Any) -> 'SourceTable':
        """Initializes the Source Table Parser.

        Args:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments described below

        Keyword Arguments:
            source_stats (bool): Whether to parse source statistics
            n_jobs (int): Number of files to run in parallel
            source_extensions (list[str]): List of file extensions to parse
        """
        self.source_stats = kwargs.get("source_stats", False)
        self.n_jobs = kwargs.get("n_jobs", -1)
        self.source_extensions = kwargs.get("source_extensions", SOURCE_EXT_LIST)

    def parse(self, session: Session, pathobj: Edk2Path, id: str, env: dict) -> None:
        """Parse the workspace and update the database."""
        ws = Path(pathobj.WorkspacePath)
        self.pathobj = pathobj

        start = time.time()
        files = []
        for src in self.source_extensions:
            files.extend(list(ws.rglob(src)))
        files = [file for file in files if not file.is_relative_to(ws / "Build")]
        src_entries = Parallel(n_jobs=self.n_jobs)(delayed(self._parse_file)(filename) for filename in files)

        existing_source = {source.path: source for source in session.query(Source).all()}
        to_add = []
        for source in src_entries:
            if source.path not in existing_source:
                existing_source[source.path] = source
                to_add.append(source)
            else:
                to_add.append(existing_source[source.path])
                to_add[-1].code_lines = source.code_lines
                to_add[-1].comment_lines = source.comment_lines
                to_add[-1].blank_lines = source.blank_lines

        session.add_all(to_add)
        session.commit()

        logging.debug(
            f"{self.__class__.__name__}: Parsed {len(src_entries)} files; "
            f"took {round(time.time() - start, 2)} seconds.")

    def _parse_file(self, filename: Path) -> dict:
        """Parse a C file and return the results."""
        license = ""
        with open(filename, 'r', encoding='cp850') as f:
            lines = f.readlines()
            for line in lines:
                match = re.search(r"SPDX-License-Identifier:\s*(.*)$", line)  # TODO: This is not a standard format.
                if match:
                    license = match.group(1)

        total_lines = len(lines)
        code_lines = total_lines
        comment_lines = 0
        blank_lines = 0
        if self.source_stats:
            code = SourceAnalysis.from_file(filename, "_", fallback_encoding="utf-8")
            code_lines = code.code_count
            comment_lines = code.documentation_count
            blank_lines = code.empty_count

        path = self.pathobj.GetEdk2RelativePathFromAbsolutePath(filename.as_posix())
        return Source(
            path=path,
            license=license or 'Unknown',
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
        )
