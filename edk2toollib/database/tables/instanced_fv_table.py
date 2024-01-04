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
from pathlib import Path
from typing import Any

from edk2toollib.database import Fv, InstancedInf, Session
from edk2toollib.database.tables import TableGenerator
from edk2toollib.uefi.edk2.parsers.fdf_parser import FdfParser as FdfP
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class InstancedFvTable(TableGenerator):
    """A Table Generator that parses a single FDF file and generates a table containing FV information.

    !!! warning
        This table generator relies on the instanced_inf_table generator to be run first.
    """  # noqa: E501

    INFOPTS = re.compile(r'(RuleOverride|file_guid|version|ui|use)\s*=.+\s+(.+\.inf)', re.IGNORECASE)

    def __init__(self, *args: Any, **kwargs: Any) -> 'InstancedFvTable':
        """Initialize the query with the specific settings."""

    def parse(self, session: Session, pathobj: Edk2Path, env_id, env) -> None:
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

        all_components = {inf.path: inf for inf in session.query(InstancedInf).filter_by(env=env_id, cls=None).all()}
        for fv in fdfp.FVs:

            inf_list = []  # Some INF's have extra options. We only need the INF
            for inf in fdfp.FVs[fv]["Infs"]:
                options = InstancedFvTable.INFOPTS.findall(inf)
                if len(options) > 0:
                    inf = options[0][1]

                # Convert to absolute, and back to relative to ensure we get the closest pp relative path
                # i.e. if we have two package paths: ("MyPP", and "MyPP/Subfolder"), in the FDF, devs
                # can specify INFs are either ("Subfolder/MyPkg/../MyPkg.inf" or "MyPkg/../MyPkg.inf")
                # However in the database, we want the closest match, i.e. "MyPkg/../MyPkg.inf", even if
                # they are providing ("Subfolder/MyPkg/../MyPkg.inf"). "GetEdk2RelativePathFromAbsolutePath"
                # always returns the relative path from the closest package path.
                inf = self.pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(inf)
                inf = self.pathobj.GetEdk2RelativePathFromAbsolutePath(inf)
                inf_list.append(Path(inf).as_posix())

            filtered = []
            for inf in inf_list:
                if inf not in all_components:
                    logging.error(f'INF [{inf}] not found in database.')
                else:
                    filtered.append(inf)

            fv = Fv(
                env = env_id,
                name = fv,
                fdf = self.fdf,
                # infs = [all_components.get(inf) for inf in inf_list]
                infs = [all_components.get(inf) for inf in filtered]
            )
            session.add(fv)
            session.commit()
