# @file license_query.py
# A Query that reads the database and returns files missing a license identifier.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
# ruff: noqa: F811
"""A Query that reads the database and returns files missing a license identifier."""
from edk2toollib.database import AdvancedQuery, Edk2DB, Query


class LicenseQuery(AdvancedQuery):
    """A Query that reads the database and returns files missing a license identifier."""
    def __init__(self, *args, **kwargs) -> None:
        """Initializes the LicenseQuery with the specified kwargs.

        Arguments:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments expanded below.

        Keyword Arguments:
            include (list[str]): A list of strings to search for in the file path name
            exclude (list[str]): A list of strings to exclude in the file path name
        """
        self.include = kwargs.get('include', None)
        self.exclude = kwargs.get('exclude', None)

        if isinstance(self.include, str):
            self.include = [self.include]
        if isinstance(self.exclude, str):
            self.exclude = [self.exclude]

    def run(self, db: Edk2DB):
        """Runs the query."""
        table = db.table("source")

        regex = "^"
        if self.include:
            regex += f"(?=.*({'|'.join(self.include)}))"
        if self.exclude:
            regex += f"(?!.*({'|'.join(self.exclude)})).*$"

        result = table.search((Query().LICENSE == "") & (Query().PATH.search(regex)))

        return self.columns(['PATH', 'LICENSE'], result)
