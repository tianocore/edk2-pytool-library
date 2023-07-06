# @file inf_table.py
# A module to run a table generator that parses all INF files in the workspace and generates a table of information
# about each INF.
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to run generate a table containing information about each INF in the workspace."""
import logging
import time
from pathlib import Path

from joblib import Parallel, delayed
from tinyrecord import transaction

from edk2toollib.database import Edk2DB, TableGenerator
from edk2toollib.uefi.edk2.parsers.inf_parser import InfParser as InfP


class InfTable(TableGenerator):
    """A Table Generator that parses all INF files in the workspace and generates a table.

    Generates a table with the following schema:

    ``` py
    table_name = "inf"
    |----------------------------------------------------------------------------------------------------------------------------|
    | GUID | LIBRARY_CLASS | PATH | PHASES | SOURCES_USED | LIBRARIES_USED | PROTOCOLS_USED | GUIDS_USED | PPIS_USED | PCDS_USED |
    |----------------------------------------------------------------------------------------------------------------------------|
    ```
    """  # noqa: E501
    def __init__(self, *args, **kwargs):
        """Initializes the INF Table Parser.

        Args:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments described below

        Keyword Arguments:
            n_jobs (int): Number of files to run in parallel
        """
        self.n_jobs = kwargs.get("n_jobs", -1)

    def parse(self, db: Edk2DB) -> None:
        """Parse the workspace and update the database."""
        ws = Path(db.pathobj.WorkspacePath)
        inf_table = db.table("inf", cache_size=None)
        inf_entries = []

        start = time.time()
        files = list(ws.glob("**/*.inf"))
        files = [file for file in files if not file.is_relative_to(ws / "Build")]
        inf_entries = Parallel(n_jobs=self.n_jobs)(delayed(self._parse_file)(ws, fname, db.pathobj) for fname in files)
        logging.debug(
            f"{self.__class__.__name__}: Parsed {len(inf_entries)} .inf files took; "
            f"{round(time.time() - start, 2)} seconds.")

        with transaction(inf_table) as tr:
            tr.insert_multiple(inf_entries)

    def _parse_file(self, ws, filename, pathobj) -> dict:
        inf_parser = InfP().SetEdk2Path(pathobj)
        inf_parser.ParseFile(filename)

        pkg = pathobj.GetContainingPackage(str(inf_parser.Path))
        path = Path(inf_parser.Path).as_posix()
        if pkg:
            path = path[path.find(pkg):]
        data = {}
        data["GUID"] = inf_parser.Dict.get("FILE_GUID", "")
        data["LIBRARY_CLASS"] = inf_parser.LibraryClass
        data["PATH"] = Path(path).as_posix()
        data["PHASES"] = inf_parser.SupportedPhases
        data["SOURCES_USED"] = inf_parser.Sources
        data["BINARIES_USED"] = inf_parser.Binaries
        data["LIBRARIES_USED"] = inf_parser.LibrariesUsed
        data["PROTOCOLS_USED"] = inf_parser.ProtocolsUsed
        data["GUIDS_USED"] = inf_parser.GuidsUsed
        data["PPIS_USED"] = inf_parser.PpisUsed
        data["PCDS_USED"] = inf_parser.PcdsUsed

        return data
