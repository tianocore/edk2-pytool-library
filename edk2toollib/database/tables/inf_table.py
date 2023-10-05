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
from sqlite3 import Cursor

from joblib import Parallel, delayed

from edk2toollib.database.tables.base_table import TableGenerator
from edk2toollib.uefi.edk2.parsers.inf_parser import InfParser as InfP
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

CREATE_INF_TABLE = '''
CREATE TABLE IF NOT EXISTS inf (
    path TEXT PRIMARY KEY,
    guid TEXT,
    library_class TEXT,
    package TEXT,
    module_type TEXT
);
'''

INSERT_JUNCTION_ROW = '''
INSERT INTO junction (env, table1, key1, table2, key2)
VALUES (?, ?, ?, ?, ?)
'''

INSERT_INF_ROW = '''
INSERT OR REPLACE INTO inf (path, guid, library_class, package, module_type)
VALUES (?, ?, ?, ?, ?)
'''

class InfTable(TableGenerator):
    """A Table Generator that parses all INF files in the workspace and generates a table."""
    # TODO: Add phase, protocol, guid, ppi, pcd tables and associations once necessary
    def __init__(self, *args, **kwargs):
        """Initializes the INF Table Parser.

        Args:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments described below

        Keyword Arguments:
            n_jobs (int): Number of files to run in parallel
        """
        self.n_jobs = kwargs.get("n_jobs", -1)

    def create_tables(self, db_cursor: Cursor) -> None:
        """Create the tables necessary for this parser."""
        db_cursor.execute(CREATE_INF_TABLE)

    def parse(self, db_cursor: Cursor, pathobj: Edk2Path, env_id: str, env: dict) -> None:
        """Parse the workspace and update the database."""
        ws = Path(pathobj.WorkspacePath)
        inf_entries = []

        start = time.time()
        files = list(ws.glob("**/*.inf"))
        files = [file for file in files if not file.is_relative_to(ws / "Build")]
        inf_entries = Parallel(n_jobs=self.n_jobs)(delayed(self._parse_file)(fname, pathobj) for fname in files)
        logging.debug(
            f"{self.__class__.__name__}: Parsed {len(inf_entries)} .inf files took; "
            f"{round(time.time() - start, 2)} seconds.")

        # Insert the data into the database
        for inf in inf_entries:
            row = (inf["PATH"], inf["GUID"], inf["LIBRARY_CLASS"], inf["PACKAGE"], inf["MODULE_TYPE"])
            db_cursor.execute(INSERT_INF_ROW, row)

            for library in inf["LIBRARIES_USED"]:
                row = (env_id, "inf", inf["PATH"], "library_class", library)
                db_cursor.execute(INSERT_JUNCTION_ROW, row)

            for source in inf["SOURCES_USED"]:
                row = (env_id, "inf", inf["PATH"], "source", source)
                db_cursor.execute(INSERT_JUNCTION_ROW, row)

    def _parse_file(self, filename, pathobj) -> dict:
        inf_parser = InfP().SetEdk2Path(pathobj)
        inf_parser.ParseFile(filename)

        pkg = pathobj.GetContainingPackage(str(inf_parser.Path))
        path = Path(inf_parser.Path).as_posix()

        # Resolve source file paths when they contain ".."
        source_list = []
        for source in inf_parser.Sources:
            source = (Path(filename).parent / source).resolve().as_posix()
            if pkg is not None:
                source_list.append(source[source.find(pkg):])
            else:
                source_list.append(source)

        if pkg:
            path = path[path.find(pkg):]
        data = {}
        data["GUID"] = inf_parser.Dict.get("FILE_GUID", "")
        data["LIBRARY_CLASS"] = inf_parser.LibraryClass or None
        data["PATH"] = Path(path).as_posix()
        data["PHASES"] = inf_parser.SupportedPhases
        data["SOURCES_USED"] = source_list
        data["BINARIES_USED"] = inf_parser.Binaries
        data["LIBRARIES_USED"] = inf_parser.LibrariesUsed
        data["PROTOCOLS_USED"] = inf_parser.ProtocolsUsed
        data["GUIDS_USED"] = inf_parser.GuidsUsed
        data["PPIS_USED"] = inf_parser.PpisUsed
        data["PCDS_USED"] = inf_parser.PcdsUsed
        data["PACKAGE"] = pkg
        data["MODULE_TYPE"] = inf_parser.Dict.get("MODULE_TYPE", None)

        return data
