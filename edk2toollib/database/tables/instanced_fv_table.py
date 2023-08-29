# @file instaced_fv.py
# A module to run a table generator that uses a fdf and environment information to generate a table of information
# about instanced fvs where each row is a unique fv.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to generate a table containing fv information."""
import re
from pathlib import Path

from tinyrecord import transaction

from edk2toollib.database import Edk2DB, TableGenerator
from edk2toollib.uefi.edk2.parsers.fdf_parser import FdfParser as FdfP


class InstancedFvTable(TableGenerator):
    """A Table Generator that parses a single FDF file and generates a table containing FV information.

    Generates a table with the following schema:

    ``` py
    table_name = "instanced_fv"
    |------------------------------------------------------|
    | FV_NAME | FDF | PATH | TARGET | INF_LIST | FILE_LIST |
    |------------------------------------------------------|
    ```
    """  # noqa: E501

    RULEOVERRIDE = re.compile(r'RuleOverride\s*=.+\s+(.*\.inf)', re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        """Initialize the query with the specific settings."""
        self.env = kwargs.pop("env")
        self.dsc = self.env["ACTIVE_PLATFORM"]
        self.fdf = self.env["FLASH_DEFINITION"]
        self.arch = self.env["TARGET_ARCH"].split(" ")
        self.target = self.env["TARGET"]

    def parse(self, db: Edk2DB) -> None:
        """Parse the workspace and update the database."""
        self.pathobj = db.pathobj
        self.ws = Path(self.pathobj.WorkspacePath)

        # Our DscParser subclass can now parse components, their scope, and their overrides
        fdfp = FdfP().SetEdk2Path(self.pathobj)
        fdfp.SetInputVars(self.env)
        fdfp.ParseFile(self.fdf)

        table_name = 'instanced_fv'
        table = db.table(table_name, cache_size=None)

        entry_list = []
        for fv in fdfp.FVs:

            inf_list = []  # Some INF's start with RuleOverride. We only need the INF
            for inf in fdfp.FVs[fv]["Infs"]:
                if inf.lower().startswith("ruleoverride"):
                    inf = InstancedFvTable.RULEOVERRIDE.findall(inf)[0]
                if Path(inf).is_absolute():
                    inf = str(Path(self.pathobj.GetEdk2RelativePathFromAbsolutePath(inf)))
                inf_list.append(Path(inf).as_posix())

            entry_list.append({
                "FV_NAME": fv,
                "FDF": Path(self.fdf).name,
                "PATH": self.fdf,
                "INF_LIST": inf_list,
                "FILE_LIST": fdfp.FVs[fv]["Files"]
            })

        with transaction(table) as tr:
            tr.insert_multiple(entry_list)
