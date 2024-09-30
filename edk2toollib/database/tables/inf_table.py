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
from typing import Any

from joblib import Parallel, delayed

from edk2toollib.database import Inf, Library, Session, Source
from edk2toollib.database.tables import TableGenerator
from edk2toollib.uefi.edk2.parsers.inf_parser import InfParser as InfP
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class InfTable(TableGenerator):
    """A Table Generator that parses all INF files in the workspace and generates a table."""

    # TODO: Add phase, protocol, guid, ppi, pcd tables and associations once necessary
    def __init__(self, *args: Any, **kwargs: Any) -> "InfTable":
        """Initializes the INF Table Parser.

        Args:
            args (any): non-keyword arguments
            kwargs (any): keyword arguments described below

        Keyword Arguments:
            n_jobs (int): Number of files to run in parallel
        """
        self.n_jobs = kwargs.get("n_jobs", -1)

    def parse(self, session: Session, pathobj: Edk2Path, env_id: str, env: dict) -> None:
        """Parse the workspace and update the database."""
        ws = Path(pathobj.WorkspacePath)
        inf_entries = []

        start = time.time()
        files = list(ws.glob("**/*.inf"))
        files = [file for file in files if not file.is_relative_to(ws / "Build")]
        inf_entries = Parallel(n_jobs=self.n_jobs)(delayed(self._parse_file)(fname, pathobj) for fname in files)

        all_inf = {inf.path: inf for inf in session.query(Inf).all()}
        all_source = {source.path: source for source in session.query(Source).all()}
        all_libs = {lib.name: lib for lib in session.query(Library).all()}
        to_add = []
        for entry, source_list, lib_list in inf_entries:
            # Could parse a Windows INF file, which is not a EDKII INF file
            # and won't have a guid. GUIDS are required for INFs so we can
            # assume if it does not have a guid, its the wrong type of INF
            if entry.guid == "":
                continue
            if entry.path in all_inf:
                continue
            for source in source_list:
                if source not in all_source:
                    all_source[source] = Source(path=source)
                entry.sources.append(all_source[source])
            for lib in lib_list:
                if lib not in all_libs:
                    all_libs[lib] = Library(name=lib)
                entry.libraries.append(all_libs[lib])
            to_add.append(entry)
            all_inf[entry.path] = entry

        session.add_all(to_add)

        logging.debug(
            f"{self.__class__.__name__}: Parsed {len(inf_entries)} .inf files took; "
            f"{round(time.time() - start, 2)} seconds."
        )

    def _parse_file(self, filename: str, pathobj: Edk2Path) -> dict:
        inf_parser = InfP().SetEdk2Path(pathobj)
        inf_parser.ParseFile(filename)

        pkg = pathobj.GetContainingPackage(str(inf_parser.Path))
        path = Path(pathobj.GetEdk2RelativePathFromAbsolutePath(str(inf_parser.Path))).as_posix()

        # Make source files package path relative and resolve ".." in paths
        source_list = []
        for source in inf_parser.Sources:
            source = (Path(filename).parent / source).resolve()
            source = Path(pathobj.GetEdk2RelativePathFromAbsolutePath(str(source))).as_posix()
            source_list.append(source)

        return (
            Inf(
                path=Path(path).as_posix(),
                guid=inf_parser.Dict.get("FILE_GUID", ""),
                library_class=inf_parser.LibraryClass or None,
                package_name=pkg,
                module_type=inf_parser.Dict.get("MODULE_TYPE", None),
            ),
            source_list,
            inf_parser.LibrariesUsed,
        )
