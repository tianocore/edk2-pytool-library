# @file edk2_db.py
# A class for interacting with a database implemented using json.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A class for interacting with a database implemented using json."""
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class Base(DeclarativeBase):
    """The base class for creating database table models.

    This class should be the subclass for any table model that will be used with Edk2DB.
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
        ```
    """
    Base = Base
    def __init__(self: 'Edk2DB', db_path: str, pathobj: Edk2Path = None, **kwargs: dict[str,Any]) -> 'Edk2DB':
        """Initializes the database.

        Args:
            db_path: Path to create or load the database from
            pathobj: Edk2Path object for the workspace
            **kwargs: None
        """
        self.pathobj = pathobj
        self.clear_parsers()
        self.engine = create_engine(f"sqlite:///{db_path}", **kwargs)
        self.Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Session:
        """Provides a context manager for a session with the database.

        Handles commiting changes and rolling back if an exception is raised.
        """
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def register(self, *parsers: 'TableGenerator') -> None:
        """Registers a one or more table generators.

        Args:
            *parsers: One or more instantiated TableGenerator object
        """
        for parser in parsers:
            self._parsers.append(parser)

    def clear_parsers(self) -> None:
        """Empties the list of registered table generators."""
        self._parsers = []

    def parse(self, env: dict) -> None:
        """Runs all registered table parsers against the database.

        !!! note
            To enable queries to differentiate between two parses, an environment table is always created if it does
            not exist, and a row is added for each call of this command.
        """
        id = str(uuid.uuid4().hex)

        # Fill all tables
        for table in self._parsers:
            logging.debug(f"[{table.__class__.__name__}] starting...")
            t = time.time()
            with self.session() as session:
                table.parse(session, self.pathobj, id, env)
            logging.debug(f"Finished in {round(time.time() - t, 2)}")

class TableGenerator:
    """An interface for a parser that generates a sqlite3 table maintained by Edk2DB.

    Allows you to parse a workspace, file, etc, and load the contents into the database as rows in a table.

    Edk2Db provides a connection to a sqlite3 database and will commit any changes made during `parse` once
    the parser has finished executing and has returned. Review sqlite3 documentation for more information on
    how to interact with the database.
    """
    def __init__(self, *args, **kwargs):
        """Initialize the query with the specific settings."""

    def parse(self, session: Session, pathobj: Edk2Path, id: str, env: dict) -> None:
        """Execute the parser and update the database."""
        raise NotImplementedError
