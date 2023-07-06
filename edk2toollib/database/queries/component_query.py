# @file component_query.py
# A Query that reads the database and returns information about an instanced component.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A Query that reads the database and returns information about an instanced component."""
from edk2toollib.database import AdvancedQuery, Edk2DB, Query


class ComponentQuery(AdvancedQuery):
    """A query that provides information about an instanced Component."""
    def __init__(self, *args, **kwargs) -> None:
        """Initializes the ComponentQuery with the specified kwargs.

        !!! note
            If the database stores multiple builds of data with different environments,
            that environment information should be stored in a `environment` table, and
            that should be linked in the `instanced_inf` via a ENV column.

        Arguments:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments expanded below.

        Keyword Arguments:
            component (string): The component to get info on; returns all components if empty
            env_idx (int): The index in the `environment` table that represents
                the environment used for parsing.

        """
        self.component = kwargs.get('component', "")
        self.env_id = kwargs.get('env_id', None)

    def run(self, db: Edk2DB):
        """Runs the query."""
        table_name = "instanced_inf"
        table = db.table(table_name)

        if self.env_id is not None:
            entries = table.search((Query().PATH.search(self.component))
                                   & ~(Query().COMPONENT.exists())
                                   & (Query().ENVIRONMENT_ID == self.env_id))
        else:
            entries = table.search((Query().PATH.search(self.component))
                                   & ~(Query().COMPONENT.exists()))

        return self.columns(["NAME", "MODULE_TYPE", "ARCH", "LIBRARIES_USED"], entries)
