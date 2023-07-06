# @file library_query.py
# A Query that reads the database and returns all instances of a given LIBRARY_CLASS
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A Query that reads the database and returns all instances of a given LIBRARY_CLASS."""
from edk2toollib.database import AdvancedQuery, Edk2DB, Query


class LibraryQuery(AdvancedQuery):
    """A query that generates a list of library instances for a given library."""
    def __init__(self, *args, **kwargs) -> None:
        """Initializes the LibraryQuery with the specified kwargs.

        Arguments:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments expanded below.

        Keyword Arguments:
            library (string): The library to get all instances of.
        """
        self.library = kwargs.get('library', "")

    def run(self, db: Edk2DB):
        """Runs the query."""
        table_name = "inf"
        table = db.table(table_name)

        result = table.search((Query().LIBRARY_CLASS != "") & (Query().LIBRARY_CLASS.matches(self.library)))
        return self.columns(["LIBRARY_CLASS", "PATH"], result)
