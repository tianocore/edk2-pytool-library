# @file instaced_fv.py
# A module to run a table generator that uses a fdf and environment information to generate a table of information
# about instanced fvs where each row is a unique fv.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to generate a table containing fv information."""
import logging
import re
import sqlite3
from pathlib import Path

from edk2toollib.database.tables.base_table import TableGenerator
from edk2toollib.uefi.edk2.parsers.fdf_parser import FdfParser as FdfP
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

CREATE_INSTANCED_FV_TABLE = """
CREATE TABLE IF NOT EXISTS instanced_fv (
    env INTEGER,
    fv_name TEXT,
    fdf TEXT,
    path TEXT
)
"""

INSERT_INSTANCED_FV_ROW = """
INSERT INTO instanced_fv (env, fv_name, fdf, path)
VALUES (?, ?, ?, ?)
"""

INSERT_JUNCTION_ROW = '''
INSERT INTO junction (env, table1, key1, table2, key2)
VALUES (?, ?, ?, ?, ?)
'''

class InstancedFvTable(TableGenerator):
    """A Table Generator that parses a single FDF file and generates a table containing FV information."""  # noqa: E501

    RULEOVERRIDE = re.compile(r'RuleOverride\s*=.+\s+(.+\.inf)', re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        """Initialize the query with the specific settings."""


    def create_tables(self, db_cursor: sqlite3.Cursor) -> None:
        """Create the tables necessary for this parser."""
        db_cursor.execute(CREATE_INSTANCED_FV_TABLE)

    def parse(self, db_cursor: sqlite3.Cursor, pathobj: Edk2Path, env_id, env) -> None:
        """Parse the workspace and update the database."""
        self.pathobj = pathobj
        self.ws = Path(self.pathobj.WorkspacePath)
        self.env = env
        self.env_id = env_id
        self.dsc = self.env.get("ACTIVE_PLATFORM", None)
        self.fdf = self.env.get("FLASH_DEFINITION", None)
        self.arch = self.env["TARGET_ARCH"].split(" ")
        self.target = self.env["TARGET"]

        if self.dsc is None or self.fdf is None:
            logging.debug("DSC or FDF not found in environment. Skipping InstancedFvTable")
            return

        # Our DscParser subclass can now parse components, their scope, and their overrides
        fdfp = FdfP().SetEdk2Path(self.pathobj)
        fdfp.SetInputVars(self.env)
        fdfp.ParseFile(self.fdf)

        for fv in fdfp.FVs:

            inf_list = []  # Some INF's start with RuleOverride. We only need the INF
            for inf in fdfp.FVs[fv]["Infs"]:
                if inf.lower().startswith("ruleoverride"):
                    inf = InstancedFvTable.RULEOVERRIDE.findall(inf)[0]
                if Path(inf).is_absolute():
                    inf = str(Path(self.pathobj.GetEdk2RelativePathFromAbsolutePath(inf)))
                inf_list.append(Path(inf).as_posix())

            row = (self.env_id, fv, Path(self.fdf).name, self.fdf)
            db_cursor.execute(INSERT_INSTANCED_FV_ROW, row)

            for inf in inf_list:
                row = (self.env_id, "instanced_fv", fv, "inf", inf)
                db_cursor.execute(INSERT_JUNCTION_ROW, row)
