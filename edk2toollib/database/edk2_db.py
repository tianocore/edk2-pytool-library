# @file edk2_db.py
# A class for interacting with a database implemented using json.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A class for interacting with a database implemented using json."""
import logging
import sqlite3
import time
import uuid
from typing import Any, Optional, Type

from edk2toollib.database.tables import EnvironmentTable
from edk2toollib.database.tables.base_table import TableGenerator
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

CREATE_JUNCTION_TABLE = """
CREATE TABLE IF NOT EXISTS junction (
    env TEXT,
    table1 TEXT,
    key1 TEXT,
    table2 TEXT,
    key2 TEXT
)
"""

CREATE_JUNCTION_INDEX = """
CREATE INDEX IF NOT EXISTS junction_idx
ON junction (env);
"""

class Edk2DB:
    """A SQLite3 database manager for a EDKII workspace.

    This class provides the ability to register parsers that will create / update tables in the database. This will
    create a SQLite datbase file that can be queried using any SQLite3 client. VSCode provides multiple extensions
    for viewing and interacting with the database. Queries can also be created and run in python using the sqlite3
    module that comes with python.

    Edk2DB can, and should, be used as a context manager to ensure that the database is closed properly. If
    not using as a context manager, the `db.connection.commit()` and `db.connection.close()` must be used to cleanly
    close the database.

    Attributes:
        connection (sqlite3.Connection): The connection to the database

    !!! note
        Edk2DB provides a table called `junction` that can be used to make associations between tables. It has the
        following schema: `env_id, table1, key1, table2, key2`.

    Example:
        ```python
        from edk2toollib.database.parsers import *
        table = "..."
        with Edk2DB(Path("path/to/db.db"), edk2path) as db:
            db.register(Parser1(), Parser2(), Parser3())
            db.parse()

            db.connection.execute("SELECT * FROM ?", table)
    """
    def __init__(self: 'Edk2DB', db_path: str, pathobj: Edk2Path = None, **kwargs: dict[str,Any]) -> 'Edk2DB':
        """Initializes the database.

        Args:
            db_path: Path to create or load the database from
            pathobj: Edk2Path object for the workspace
            **kwargs: None
        """
        self.pathobj = pathobj
        self.clear_parsers()
        self.connection = sqlite3.connect(db_path)

    def __enter__(self: 'Edk2DB') -> 'Edk2DB':
        """Enables the use of the `with` statement."""
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[Any]  # noqa: ANN401
    ) -> None:
        """Enables the use of the `with` statement."""
        self.connection.commit()
        self.connection.close()

    def register(self, *parsers: 'TableGenerator') -> None:
        """Registers a one or more table generators.

        Args:
            *parsers: One or more instantiated TableGenerator object
        """
        for parser in parsers:
            self._parsers.append(parser)

    def clear_parsers(self) -> None:
        """Empties the list of registered table generators."""
        self._parsers = [EnvironmentTable()]

    def parse(self, env: dict) -> None:
        """Runs all registered table parsers against the database.

        !!! note
            To enable queries to differentiate between two parses, an environment table is always created if it does
            not exist, and a row is added for each call of this command.
        """
        self.connection.execute(CREATE_JUNCTION_TABLE)
        self.connection.execute(CREATE_JUNCTION_INDEX)
        id = str(uuid.uuid4().hex)

        # Create all tables
        for table in self._parsers:
            table.create_tables(self.connection.cursor())

        # Fill all tables
        for table in self._parsers:
            logging.debug(f"[{table.__class__.__name__}] starting...")
            t = time.time()
            table.parse(self.connection.cursor(), self.pathobj, id, env)
            self.connection.commit()
            logging.debug(f"Finished in {round(time.time() - t, 2)}")
