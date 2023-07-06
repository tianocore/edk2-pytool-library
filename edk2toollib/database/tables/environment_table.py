# @file environment_table.py
# A module to run a table generator that creates or appends to a table with environment information."
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to run a table generator that creates or appends to a table with environment information."""
from datetime import date

from tinyrecord import transaction

from edk2toollib.database import Edk2DB, TableGenerator


class EnvironmentTable(TableGenerator):
    """A Workspace parser that records import environment information for a given parsing execution.

    Generates a table with the following schema:


    ``` py
    table_name = "environment"
    |--------------------------------------|
    | DATE | VERSION | ENV | PACKAGES_PATH |
    |--------------------------------------|
    ```
    """  # noqa: E501
    def __init__(self, *args, **kwargs):
        """Initialize the query with the specific settings."""
        self.env = kwargs.pop("env")

    def parse(self, db: Edk2DB) -> None:
        """Parses the environment and adds the data to the table."""
        table_name = 'environment'
        table = db.table(table_name, cache_size=None)
        today = date.today()

        # Pull out commonly used environment variables as their own entry rather than in the dict.
        version = self.env.pop('VERSION', "UNKNOWN")
        pp = self.env.pop('PACKAGES_PATH', [])

        entry = {
            "DATE": str(today),
            "VERSION": version,
            "ENV": self.env,
            "PACKAGES_PATH": pp,
        }

        with transaction(table) as tr:
            tr.insert(entry)
