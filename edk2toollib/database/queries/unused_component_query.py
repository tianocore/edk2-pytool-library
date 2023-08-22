# @file unused_component_query.py
# A Query that reads the database and returns all components and libraries defined in the DSC but unused in the FDF.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A Query that reads the database and returns all components / libraries defined in the DSC but unused in the FDF."""
from typing import Union

from edk2toollib.database import AdvancedQuery, Edk2DB, Query


class UnusedComponentQuery(AdvancedQuery):
    """A query that returns any unused components for a specific build."""
    def __init__(self, *args, **kwargs) -> None:
        """Initializes the UnusedComponentQuery with the specified kwargs.

        !!! note
            If the database stores multiple builds of data with different environments,
            that environment information should be stored in a `environment` table, and
            that should be linked in the `instanced_inf` via a ENV column.

        Arguments:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments expanded below.

        Keyword Arguments:
            ignore_app (bool): Whether to ingore UEFI_APPLICATIONs or not
            env_idx (int): The index in the `environment` table that represents
                the environment to use for parsing.
        """
        self.ignore_app = kwargs.get('ignore_app', False)
        self.env_id = kwargs.get('env_id', None)

    def run(self, db: Edk2DB) -> Union[str, str]:
        """Returns (unused_components, unused_libraries)."""
        dsc_infs = db.table("instanced_inf")
        fdf_fvs = db.table("instanced_fv")

        dsc_components = []
        fdf_components = []

        if self.env_id is not None:
            dsc_rows = dsc_infs.search((~Query().COMPONENT.exists()) & (Query().ENVIRONMENT_ID == self.env_id))
            fv_rows = fdf_fvs.search(Query().ENVIRONMENT_ID == self.env_id)
        else:
            dsc_rows = dsc_infs.search(~Query().COMPONENT.exists())
            fv_rows = fdf_fvs.all()

        # Grab all components in the DSC
        for entry in dsc_rows:
            if self.ignore_app and entry["MODULE_TYPE"] == "UEFI_APPLICATION":
                continue
            dsc_components.append(entry["PATH"])

        # Grab all components from the fdf
        for fv in fv_rows:
            fdf_components.extend(fv["INF_LIST"])

        unused_components = set(dsc_components) - set(fdf_components)
        used_components = set(fdf_components)

        unused_library_list = []
        used_library_list = []

        # Grab all libraries used by unused_components
        for component in unused_components:
            self._recurse_inf(component, dsc_infs, unused_library_list)

        # Grab all libraries used by used_components
        for component in used_components:
            self._recurse_inf(component, dsc_infs, used_library_list)

        unused_libraries = set(unused_library_list) - set(used_library_list)

        return (list(unused_components), list(unused_libraries))

    def _recurse_inf(self, inf, table, library_list):
        if inf in library_list:
            return

        if self.env_id is not None:
            search_results = table.search((Query().PATH == inf) & (Query().ENVIRONMENT_ID == self.env_id))
        else:
            search_results = table.search(Query().PATH == inf)

        for result in search_results:
            # Only mark a inf as visited if it is a library
            if "COMPONENT" in result:
                library_list.append(inf)

            for inf in result["LIBRARIES_USED"]:
                self._recurse_inf(inf[1], table, library_list)
