# @file package_table.py
# A module to associate the packages in a workspace with the repositories they come from.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to generate a table containing information about a package."""
from pathlib import Path
from sqlite3 import Cursor
from typing import Any

import git

from edk2toollib.database.tables.base_table import TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

CREATE_PACKAGE_TABLE = """
CREATE TABLE IF NOT EXISTS package (
    name TEXT PRIMARY KEY,
    repository TEXT
)
"""

INSERT_PACKAGE_ROW = """
INSERT OR REPLACE INTO package (name, repository)
VALUES (?, ?)
"""
class PackageTable(TableGenerator):
    """A Table Generator that associates packages with their repositories."""
    def __init__(self, *args: Any, **kwargs: Any) -> 'PackageTable':
        """Initializes the Repository Table Parser.

        Args:
            args (any): non-keyword arguments
            kwargs (any): None

        """

    def create_tables(self, db_cursor: Cursor) -> None:
        """Create the table necessary for this parser."""
        db_cursor.execute(CREATE_PACKAGE_TABLE)

    def parse(self, db_cursor: Cursor, pathobj: Edk2Path, id: str, env: dict) -> None:
        """Glob for packages and insert them into the table."""
        try:
            repo = git.Repo(pathobj.WorkspacePath)
        except git.InvalidGitRepositoryError:
            return

        for file in Path(pathobj.WorkspacePath).rglob("*.dec"):
            pkg = pathobj.GetContainingPackage(str(file))
            containing_repo = "BASE"
            if "origin" in repo.remotes:
                containing_repo = repo.remotes.origin.url.split("/")[-1].split(".git")[0].upper()
            elif len(repo.remotes) > 0:
                containing_repo = repo.remotes[0].url.split("/")[-1].split(".git")[0].upper()
            if repo:
                for submodule in repo.submodules:
                    if submodule.abspath in str(file):
                        containing_repo = submodule.name
                        break
            row = (pkg, containing_repo)
            db_cursor.execute(INSERT_PACKAGE_ROW, row)
