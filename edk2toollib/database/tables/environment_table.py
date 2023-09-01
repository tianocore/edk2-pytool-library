# @file environment_table.py
# A module to run a table generator that creates or appends to a table with environment information."
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to run a table generator that creates or appends to a table with environment information."""
import datetime
import sqlite3

import git

from edk2toollib.database.tables.base_table import TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

CREATE_ENV_TABLE_COMMAND = '''
CREATE TABLE IF NOT EXISTS environment (
    id TEXT PRIMARY KEY,
    date TEXT,
    version TEXT
);
'''

CREATE_ENV_VALUES_TABLE_COMMAND = '''
CREATE TABLE IF NOT EXISTS environment_values (
    id TEXT,
    key TEXT,
    value TEXT,
    FOREIGN KEY (id) REFERENCES environment(id)
);
'''

class EnvironmentTable(TableGenerator):
    """A Workspace parser that records import environment information for a given parsing execution."""  # noqa: E501
    def __init__(self, *args, **kwargs):
        """Initialize the query with the specific settings."""

    def create_tables(self, db_cursor: sqlite3.Cursor) -> None:
        """Create the tables necessary for this parser."""
        db_cursor.execute(CREATE_ENV_VALUES_TABLE_COMMAND)
        db_cursor.execute(CREATE_ENV_TABLE_COMMAND)

    def parse(self, db_cursor: sqlite3.Cursor, pathobj: Edk2Path, id, env) -> None:
        """Parses the environment and adds the data to the table."""
        dtime = datetime.datetime.now()

        try:
            version = git.Repo(pathobj.WorkspacePath).head.commit.hexsha
        except git.InvalidGitRepositoryError:
            version = "UNKNOWN"

        # Insert into environment table
        entry = (id,str(dtime),version,)
        db_cursor.execute("INSERT INTO environment (id, date,version) VALUES (?, ?, ?)", entry)

        # Insert into environment_values table
        data = [(db_cursor.lastrowid, key, value) for key, value in env.items()]
        db_cursor.executemany("INSERT INTO environment_values VALUES (?, ?, ?)", data)
