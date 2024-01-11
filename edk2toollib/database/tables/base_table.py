# @file base_table.py
# An interface for a parser that generates a sqlite3 table maintained by Edk2DB.
##
# Copyright (c) Microsoft Corporation
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""An interface for a parser that generates a sqlite3 table maintained by Edk2DB."""
import sqlite3
from typing import Any

from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class TableGenerator:
    """An interface for a parser that generates a sqlite3 table maintained by Edk2DB.

    Allows you to parse a workspace, file, etc, and load the contents into the database as rows in a table.

    Edk2Db provides a connection to a sqlite3 database and will commit any changes made during `parse` once
    the parser has finished executing and has returned. Review sqlite3 documentation for more information on
    how to interact with the database.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> 'TableGenerator':
        """Initialize the query with the specific settings."""

    def create_tables(self, db_cursor: sqlite3.Cursor) -> None:
        """Create the tables necessary for this parser."""
        raise NotImplementedError

    def parse(self, db_cursor: sqlite3.Cursor, pathobj: Edk2Path, id: str, env: dict) -> None:
        """Execute the parser and update the database."""
        raise NotImplementedError
