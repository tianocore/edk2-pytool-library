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
from typing import Any, List

from tinydb import TinyDB
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.table import Document


class Edk2DB(TinyDB):
    """A subclass of TinyDB providing advanced queries and parser management.

    This class provides the ability to register parsers that will create / update tables in the database while also
    providing the ability to run queries on the database.

    Edk2DB can be run in three modes:

    1. File Read/Write: A database will be loaded or created at the specified path. Any changes made will be written
       to the database file. This is the slowest of the three modes. Specify with Edk2DB.FILE_RW

    2. File Read Only: A database will be loaded at the specific path. Attempting to change the database will result
       in an error. This is the middle of the three in terms of performance. Specify with Edk2DB.FILE_RO

    3. In-Memory Read/Write: A database will be created in memory. Any changes made will only exist for the lifetime
       of the database object. This is the fastest of the three modes. Specify with Edk2DB.MEM_RW

    Edk2DB can, and should, be used as a context manager to ensure that the database is closed properly. If
    not using as a context manager, the `close()` method must be used to ensure that the database is closed properly
    and any changes are saved.

    When running the parse() command, the user can specify whether or not to append the results to the database. If
    not appending to the database, the entire database will be dropped before parsing.

    ```python
    # Run using File storage
    from edk2toollib.database.parsers import *
    with Edk2DB(Edk2DB.FILE_RW, pathobj=edk2path, db_path=Path("path/to/db.db")) as db:
        db.register(Parser1(), Parser2(), Parser3())
        db.parse()

    # Run using Memory storage
    from edk2toollib.database.parsers import *
    with Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path) as db:
        db.register(Parser1(), Parser2(), Parser3())
        db.parse()

    # Run some parsers in clear mode and some in append mode
    from edk2toollib.database.parsers import *
    with Edk2DB(Edk2DB.MEM_RW, pathobj=edk2path) as db:
        db.register(Parser1())
        db.parse()
        db.clear_parsers()

        db.register(Parser2(), Parser3())
        for env in env_list:
            db.parse(env=env, append=True)

    # Run Queries on specific tables or on the database
    from edk2toollib.database.queries import *
    with Edk2DB(Edk2DB.FILE_RW, pathobj=edk2path, db_path=Path("path/to/db.db")) as db:
        # Run a tinydb Query
        # https://tinydb.readthedocs.io/en/latest/usage.html#queries
        query_results = db.table("TABLENAME").search(Query().table_field == "value")

        # Run an advanced query
        query_results = db.search(AdvancedQuerySubclass(config1 = "x", config2 = "y"))
    """
    FILE_RW = 1 # Mode: File storage, Read & Write
    FILE_RO = 2 # Mode: File storage, Read Only
    MEM_RW = 3  # Mode: Memory storage, Read & Write

    def __init__(self, mode: int, **kwargs: dict[str,Any]):
        """Initializes the database.

        Args:
            mode: The mode you are opening the database with Edk2DB.FILE_RW, Edk2DB.FILE_RO, Edk2DB.MEM_RW
            **kwargs: see Keyword Arguments

        Keyword Arguments:
            db_path (str): Path to create or load the database from
            pathobj (Edk2Path): Edk2Path object for the workspace

        !!! note
            needing db_path or pathobj depends on the mode you are opening the database with.
        """
        self.pathobj = None
        self._parsers = []

        if mode == Edk2DB.FILE_RW:
            logging.debug("Database running in File Read/Write mode.")
            super().__init__(kwargs.pop("db_path"), access_mode='r+', storage=CachingMiddleware(JSONStorage))
            self.pathobj = kwargs.pop("pathobj")
        elif mode == Edk2DB.FILE_RO:
            logging.debug("Database running in File ReadOnly mode.")
            super().__init__(kwargs.pop("db_path"), access_mode='r', storage=CachingMiddleware(JSONStorage))
        elif mode == Edk2DB.MEM_RW:
            logging.debug("Database running in In-Memory Read/Write mode.")
            super().__init__(storage=MemoryStorage)
            self.pathobj = kwargs.pop("pathobj")
        else:
            raise ValueError("Unknown Database mode.")

    def register(self, *parsers: 'TableGenerator') -> None:
        """Registers a one or more table generators.

        Args:
            *parsers: One or more instantiated TableGenerator object
        """
        for parser in parsers:
            self._parsers.append(parser)

    def clear_parsers(self) -> None:
        """Empties the list of registered table generators."""
        self._parsers.clear()

    def parse(self, append: bool=False) -> None:
        """Runs all registered table parsers against the database.

        Args:
            append: Whether to append to the database or clear it first
        """
        if not append:
            self.drop_tables()

        for parser in self._parsers:
            logging.debug(f"[{parser.__class__.__name__}] starting...")
            try:
                t = time.time()
                parser.parse(self)
            except Exception as e:
                logging.error(f"[{parser.__class__.__name__}] failed.")
                logging.error(str(e))
            finally:
                logging.debug(f"[{parser.__class__.__name__}] finished in {time.time() - t:.2f}s")

    def search(self, advanced_query: 'AdvancedQuery') -> List[Document]:
        """Runs an advanced query against the database.

        Args:
            advanced_query: The query to run
        """
        return advanced_query.run(self)


class AdvancedQuery:
    """An interface for an advanced query.

    One of TinyDB's limitations is that it does not support relationships between tables (i.e. Primary Key / Foreign
    Key and JOINs). This means these types of queries are more complicated and require additional steps. An advanced
    Query is a conceptual way to grouping these extra steps in a single place and providing a single line interface
    to execute the more advanced query.

    ```python
    # An example of a simple query, an interface provided by TinyDB to run a single query against a single table
    db.table('table_name').search(Query().field == 'value' & Query().field2 == 'value2')

    # An example of an advanced query, which is run at the database level instead of the table level and can
    # run multiple queries
    db.query(MyAdvancedQuery(config1 = "a", config2 = "b"))
    ```
    """
    def __init__(self, *args, **kwargs) -> None:
        """Initialize the query with the specific settings."""

    def run(self, db: Edk2DB) -> any:
        """Run the query against the database."""
        raise NotImplementedError

    def columns(self, column_list: list[str], documents: list[Document], ):
        """Given a list of Documents, return it with only the specified columns."""
        filtered_list = []
        for document in documents:
            filtered_dict = {k: v for k, v in document.items() if k in column_list}
            filtered_list.append(Document(filtered_dict, document.doc_id))
        return filtered_list


class TableGenerator:
    """An interface for a parser that Generates an Edk2DB table.

    Allows you to parse a workspace, file, etc, and load the contents into the database as rows in a table.

    As Edk2DB is a subclass of TinyDB, it uses the same interface to interact with the database. This documentation
    can be found here: https://tinydb.readthedocs.io/en/latest/usage.html#handling-data. While TinyDB provides a
    default table to write to, it is suggested that a table be created for each parser using `db.table('table_name')`

    Common commands:
        - `table = db.table('table_name')` Get or create a table from the database
        - `table.insert(dict)` Insert a new entry into the table
        - `table.insert_multiple([dict1, dict2, ...])` Insert multiple entries into the table

    !!! warning
        Inserting many large entries into the database is slow! If you need to insert many entries, use tinyrecord's
        transaction method which uses a record-first then execute architecture that minimizes the time we are in a
        threadlock. This has been seen to cut insertion times by 90% for typical purposes.

        ```python
        from tinyrecord import transaction
        with transaction(table) as tr:
            tr.insert_multiple
        ```
    """
    def __init__(self, *args, **kwargs):
        """Initialize the query with the specific settings."""

    def parse(self, db: Edk2DB) -> None:
        """Execute the parser and update the database."""
        raise NotImplementedError
