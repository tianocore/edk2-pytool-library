# @file instanced_inf.py
# A module to run a table generator that uses a dsc and environment information to generate a table of information
# about instanced components and libraries where each row is a component or library
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module to run the InstancedInf table generator against a dsc, adding instanced inf information to the database."""
import logging
import re
from pathlib import Path
from typing import Any

from edk2toollib.database import InstancedInf, Package, Repository, Session, Source
from edk2toollib.database.tables import TableGenerator
from edk2toollib.uefi.edk2.parsers.dsc_parser import DscParser as DscP
from edk2toollib.uefi.edk2.parsers.inf_parser import InfParser as InfP
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class InstancedInfTable(TableGenerator):
    """A Table Generator that parses a single DSC file and generates a table."""
    SECTION_LIBRARY = "LibraryClasses"
    SECTION_COMPONENT = "Components"
    SECTION_REGEX = re.compile(r"\[(.*)\]")
    OVERRIDE_REGEX = re.compile(r"\<(.*)\>")

    def __init__(self, *args: Any, **kwargs: Any) -> 'InstancedInfTable':
        """Initialize the query with the specific settings."""
        self._parsed_infs = {}

    def inf(self, inf: str) -> InfP:
        """Returns a parsed INF object.

        Caches the parsed inf information to reduce multiple re-parses.
        """
        if inf in self._parsed_infs:
            infp = self._parsed_infs[inf]
        else:
            infp = InfP().SetEdk2Path(self.pathobj)
            infp.ParseFile(inf)
            self._parsed_infs[inf] = infp
        return infp

    def parse(self, session: Session, pathobj: Edk2Path, env_id: str, env: dict) -> None:
        """Parse the workspace and update the database."""
        self.pathobj = pathobj
        self.ws = Path(self.pathobj.WorkspacePath)
        self.env = env
        self.dsc = self.env["ACTIVE_PLATFORM"]
        self.arch = self.env["TARGET_ARCH"].split(" ")
        self.target = self.env["TARGET"]

        dscp = DscP().SetEdk2Path(self.pathobj)
        dscp.SetInputVars(self.env)
        dscp.ParseFile(self.dsc)

        # General Debugging
        logging.debug(f"All DSCs included in {self.dsc}:")
        for dsc in dscp.GetAllDscPaths():
            logging.debug(f"  {dsc}")

        logging.debug("Fully expanded DSC:")
        for line in dscp.Lines:
            logging.debug(f"  {line}")
        logging.debug("End of DSC")

        # Parse and insert
        inf_entries = self._build_inf_table(dscp)
        return self._insert_db_rows(session, env_id, inf_entries)

    def _insert_db_rows(self, session: Session, env_id: str, inf_entries: list) -> int:
        """Inserts data into the database.

        Inserts all inf's into the instanced_inf table and links source files and used libraries via the junction
        table.
        """
        # Insert all instanced INF rows
        rows = []
        all_sources = {source.path: source for source in session.query(Source).all()}
        all_packages = {package.name: package for package in session.query(Package).all()}
        all_repos = {
            (repo.name, repo.path): repo for repo in session.query(Repository).filter(Repository.path is not None).all()
        }
        local_repo = session.query(Repository).filter_by(path = None).first()
        for e in inf_entries:
            # Could parse a Windows INF file, which is not a EDKII INF file
            # and won't have a guid. GUIDS are required for INFs so we can
            # assume if it does not have a guid, its the wrong type of INF
            if e["GUID"] == "":
                continue
            sources = []
            for src in e["SOURCES_USED"]:
                if src in all_sources:
                    sources.append(all_sources[src])
                else:
                    sources.append(Source(path=src))
                    all_sources[src] = sources[-1]

            package = None if e["PACKAGE"] is None else all_packages.get(e["PACKAGE"])
            if package is not None:
                repo = package.repository
            else:
                def filter_search(repo: Repository) -> bool:
                    """Return the Repository that contains the INF file."""
                    if repo.path is None:
                        return False
                    return Path(self.pathobj.WorkspacePath, repo.path).as_posix() in Path(e["FULL_PATH"]).as_posix()
                repo = next(
                    filter(filter_search, all_repos.values()),
                    local_repo # Default
                )
            rows.append(
                InstancedInf(
                    env = env_id,
                    path = e["PATH"],
                    cls = e.get("LIBRARY_CLASS"),
                    name = e["NAME"],
                    arch = e["ARCH"],
                    dsc = e["DSC"],
                    component = e["COMPONENT"],
                    sources = sources,
                    package = package,
                    repository = repo,
                )
            )
        session.add_all(rows)
        session.commit()

        all_libraries = {
            (
                library.path,
                library.arch,
                library.cls,
                library.component
            ): library for library in session.query(InstancedInf).filter_by(env=env_id).all()
        }
        # Link all instanced INF rows to their used libraries
        for row, inf in zip(rows, inf_entries):
            libraries = [all_libraries.get((path, row.arch, lib, row.component)) for lib, path in inf["LIBRARIES_USED"]]
            row.libraries.extend([lib for lib in libraries if lib is not None])

        session.commit()

    def _build_inf_table(self, dscp: DscP) -> list:
        """Create the instanced inf entries, including components and libraries.

        Multiple entries of the same library will exist if multiple components use it.
        This is where we merge DSC parser information with INF parser information.
        """
        inf_entries = []
        for (inf, scope, overrides) in dscp.Components:
            # components section scope should only contain the arch.
            # module_type is only needed for libraryclasses section.
            if "." in scope:
                logging.debug(f"DSC section header unnecessarily contains MODULE_TYPE: [Components.{scope.upper()}]")
                scope = scope.split(".")[0]

            # Ignore components built with an architecture that is not in TARGET_ARCH
            arch = scope.upper()
            if arch not in self.arch:
                continue

            # Developers can set an inf path to be relative to any package path. Convert it to be the closest
            # package path relative path to the INF, which is done by `GetEdk2RelativePathFromAbsolutePath`
            inf = self.pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(inf)
            inf = self.pathobj.GetEdk2RelativePathFromAbsolutePath(inf)

            logging.debug(f"Parsing Component: [{arch}][{inf}]")
            infp = InfP().SetEdk2Path(self.pathobj)
            infp.ParseFile(inf)

            # Libraries marked as a component only have source compiled and do not link against other libraries
            if "LIBRARY_CLASS" in infp.Dict:
                continue

            # scope for libraries need to contain the MODULE_TYPE also, so we will append it, if it exists
            if "MODULE_TYPE" in infp.Dict:
                scope += f".{infp.Dict['MODULE_TYPE']}".lower()

            inf_entries += self._parse_inf_recursively(inf, None, inf, dscp.ScopedLibraryDict, overrides, scope, [])

        return inf_entries

    def _parse_inf_recursively(
        self,
        inf: str,
        library_class: str,
        component: str,
        library_dict: dict,
        override_dict: dict,
        scope: str,
        visited: list[str]
    ) -> str:
        """Recurses down all libraries starting from a single INF.

        Will immediately return if the INF has already been visited.
        """
        if inf is None:
            return []

        logging.debug(f"  Parsing Library: [{inf}]")
        visited.append(inf)
        library_instance_list = []
        library_class_list = []
        arch = scope.split(".")[0].upper()

        #
        # 0. Use the existing parser to parse the INF file. This parser parses an INF as an independent file
        #    and does not take into account the context of a DSC.
        #
        infp = self.inf(inf)

        #
        # 1. Convert all libraries to their actual instances for this component. This takes into account
        #    any overrides for this component
        #
        for lib in infp.get_libraries([arch]):
            lib = lib.split(" ")[0]
            library_instance_list.append(self._lib_to_instance(lib.lower(), scope, library_dict, override_dict))
            library_class_list.append(lib)

        #
        # 2. Append all NULL library instances if parsing the component.
        #
        if inf == component:
            for null_lib in override_dict["NULL"]:
                library_instance_list.append(null_lib)
                library_class_list.append("NULL")

            for null_lib in self._get_null_lib_instances(scope, library_dict):
                library_instance_list.append(null_lib)
                library_class_list.append("NULL")

        #
        # 3. Recursively parse used libraries
        #
        to_return = []
        for cls, instance in zip(library_class_list, library_instance_list):
            if instance is None or instance in visited:
                continue
            to_return += self._parse_inf_recursively(
                            instance, cls, component, library_dict, override_dict, scope, visited
                        )
        # Transform path to edk2 relative form (POSIX)
        def to_posix(path: str) -> str:
            if path is None:
                return None
            return Path(path).as_posix()
        library_instance_list = list(map(to_posix, library_instance_list))

        source_list = []
        full_inf = self.pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(inf)
        pkg = self.pathobj.GetContainingPackage(full_inf)
        for source in infp.get_sources([arch]):
            source = (Path(full_inf).parent / source).resolve()
            source = Path(self.pathobj.GetEdk2RelativePathFromAbsolutePath(str(source))).as_posix()
            source_list.append(source)

        # Return Paths as posix paths, which is Edk2 standard.
        to_return.append({
            "DSC": Path(self.dsc).name,
            "PATH": Path(inf).as_posix(),
            "FULL_PATH": full_inf,
            "GUID": infp.Dict.get("FILE_GUID", ""),
            "NAME": infp.Dict["BASE_NAME"],
            "LIBRARY_CLASS": library_class,
            "COMPONENT": Path(component).as_posix(),
            "MODULE_TYPE": infp.Dict["MODULE_TYPE"],
            "ARCH": arch,
            "PACKAGE": pkg,
            "SOURCES_USED": source_list,
            "LIBRARIES_USED": list(zip(library_class_list, library_instance_list)),
            "PROTOCOLS_USED": [],  # TODO
            "GUIDS_USED": [],  # TODO
            "PPIS_USED": [],  # TODO
            "PCDS_USED": infp.PcdsUsed,
        })
        return to_return

    def _lib_to_instance(
        self,
        library_class_name: str,
        scope: str,
        library_dict: dict,
        override_dict: dict
    ) -> str:
        """Converts a library name to the actual instance of the library.

        This conversion is based off the library section definitions in the DSC.
        """
        arch, module = tuple(scope.split("."))

        # NOTE: it is recognized that the below code could be reduced to have less repetitiveness,
        # but I personally believe that the below makes it more clear the order in which we search
        # for matches, and that the order is quite important.

        # https://tianocore-docs.github.io/edk2-DscSpecification/release-1.28/2_dsc_overview/27_[libraryclasses]_section_processing.html#27-libraryclasses-section-processing

        # 1. If a Library class instance (INF) is specified in the Edk2 II [Components] section (an override),
        #    and the library supports the module, then it will be used.
        if library_class_name in override_dict:
            return override_dict[library_class_name]

        # 2/3. If the Library Class instance (INF) is defined in the [LibraryClasses.$(ARCH).$(MODULE_TYPE)] section,
        #      and the library supports the module, then it will be used.
        lookup = f'{arch}.{module}.{library_class_name}'
        if lookup in library_dict:
            library_instance = self._reduce_lib_instances(module, library_dict[lookup])
            if library_instance is not None:
                return library_instance

        # 4. If the Library Class instance (INF) is defined in the [LibraryClasses.common.$(MODULE_TYPE)] section,
        #    and the library supports the module, then it will be used.
        lookup = f'common.{module}.{library_class_name}'
        if lookup in library_dict:
            library_instance = self._reduce_lib_instances(module, library_dict[lookup])
            if library_instance is not None:
                return library_instance

        # 5. If the Library Class instance (INF) is defined in the [LibraryClasses.$(ARCH)] section,
        #    and the library supports the module, then it will be used.
        lookup = f'{arch}.{library_class_name}'
        if lookup in library_dict:
            library_instance = self._reduce_lib_instances(module, library_dict[lookup])
            if library_instance is not None:
                return library_instance

        # 6. If the Library Class Instance (INF) is defined in the [LibraryClasses] section,
        #    and the library supports the module, then it will be used.
        lookup = f'common.{library_class_name}'
        if lookup in library_dict:
            library_instance = self._reduce_lib_instances(module, library_dict[lookup])
            if library_instance is not None:
                return library_instance

        logging.debug(f'scoped library contents: {library_dict}')
        logging.debug(f'override dictionary: {override_dict}')
        e = f'Cannot find library class [{library_class_name}] for scope [{scope}] when evaluating {self.dsc}'
        logging.warning(e)
        return None

    def _reduce_lib_instances(self, module: str, library_instance_list: list[str]) -> str:
        """For a DSC, multiple library instances for the same library class can exist.

        This is either due to a mistake by the developer, or because the library class
        instance only supports certain modules. That is to say a library class instance
        defining `MyLib| PEIM` and one defining `MyLib| PEI_CORE` both being defined in
        the same LibraryClasses section is acceptable.

        Due to this, we need to filter to the first library class instance that supports
        the module type.
        """
        for library_instance in library_instance_list:
            infp = self.inf(library_instance)
            if module.lower() in [phase.lower() for phase in infp.SupportedPhases]:
                # Ensure the returned path is relative to the closest package path
                library_instance = self.pathobj.GetAbsolutePathOnThisSystemFromEdk2RelativePath(library_instance)
                library_instance = self.pathobj.GetEdk2RelativePathFromAbsolutePath(library_instance)
                return library_instance
        return None

    def _get_null_lib_instances(
        self,
        scope: str,
        library_dict: dict,
    ) -> list:
        """Returns all null libraries for a given scope.

        Args:
            scope (str): The scope to search for null libraries.
            library_dict (dict): The dictionary of libraries to search through.

        Returns:
            list: A list of null libraries for the given scope.
        """
        arch, module = tuple(scope.split("."))
        null_libs = []

        lookup = f'{arch}.{module}.null'
        null_libs.extend(library_dict.get(lookup, []))

        lookup = f'common.{module}.null'
        null_libs.extend(library_dict.get(lookup, []))

        lookup = f'{arch}.null'
        null_libs.extend(library_dict.get(lookup, []))

        lookup = 'common.null'
        null_libs.extend(library_dict.get(lookup, []))

        return null_libs
