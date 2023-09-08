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
from sqlite3 import Cursor

from edk2toollib.database.tables.base_table import TableGenerator
from edk2toollib.uefi.edk2.parsers.dsc_parser import DscParser as DscP
from edk2toollib.uefi.edk2.parsers.inf_parser import InfParser as InfP
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

CREATE_INSTANCED_INF_TABLE = '''
CREATE TABLE IF NOT EXISTS instanced_inf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    env INTEGER,
    path TEXT,
    class TEXT,
    name TEXT,
    arch TEXT,
    dsc TEXT,
    component TEXT,
    FOREIGN KEY(env) REFERENCES environment(env)
)
'''

INSERT_INSTANCED_INF_ROW = '''
INSERT INTO instanced_inf (env, path, class, name, arch, dsc, component)
VALUES (?, ?, ?, ?, ?, ?, ?)
'''

INSERT_JUNCTION_ROW = '''
INSERT INTO junction (env, table1, key1, table2, key2)
VALUES (?, ?, ?, ?, ?)
'''

GET_ROW_ID = '''
SELECT id FROM instanced_inf
WHERE env = ? and path = ? and dsc = ? and (class = ? OR class IS NULL)
LIMIT 1
'''

class InstancedInfTable(TableGenerator):
    """A Table Generator that parses a single DSC file and generates a table."""
    SECTION_LIBRARY = "LibraryClasses"
    SECTION_COMPONENT = "Components"
    SECTION_REGEX = re.compile(r"\[(.*)\]")
    OVERRIDE_REGEX = re.compile(r"\<(.*)\>")

    def __init__(self, *args, **kwargs):
        """Initialize the query with the specific settings."""

    def create_tables(self, db_cursor: Cursor) -> None:
        """Create the tables necessary for this parser."""
        db_cursor.execute(CREATE_INSTANCED_INF_TABLE)

        # Prevent parsing the same INF multiple times
        self._parsed_infs = {}

    def inf(self, inf: str) -> InfP:
        """Returns a parsed INF object."""
        if inf in self._parsed_infs:
            infp = self._parsed_infs[inf]
        else:
            infp = InfP().SetEdk2Path(self.pathobj)
            infp.ParseFile(inf)
            self._parsed_infs[inf] = infp
        return infp

    def parse(self, db_cursor: Cursor, pathobj: Edk2Path, id: str, env: dict) -> None:
        """Parse the workspace and update the database."""
        self.pathobj = pathobj
        self.ws = Path(self.pathobj.WorkspacePath)
        self.id = id
        self.env = env
        self.dsc = self.env["ACTIVE_PLATFORM"] # REQUIRED
        self.fdf = self.env.get("FLASH_DEFINITION", "")  # OPTIONAL
        self.arch = self.env["TARGET_ARCH"].split(" ")  # REQUIRED
        self.target = self.env["TARGET"]  # REQUIRED

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

        # Create the instanced inf entries, including components and libraries. Multiple entries
        # of the same library will exist if multiple components use it.
        #
        # This is where we merge DSC parser information with INF parser information.
        inf_entries = self._build_inf_table(dscp)
        for e in inf_entries:
            if Path(e["PATH"]).is_absolute():
                e["PATH"] = self.pathobj.GetEdk2RelativePathFromAbsolutePath(e["PATH"])

        # add instanced_inf entries
        for e in inf_entries:
            row = (id, e["PATH"], e["LIBRARY_CLASS"] or None, e["NAME"], e["ARCH"], e["DSC"], e["COMPONENT"])
            db_cursor.execute(INSERT_INSTANCED_INF_ROW, row)

        for e in inf_entries:
            inf_id = db_cursor.execute(GET_ROW_ID, (id, e["PATH"], e["DSC"], e["LIBRARY_CLASS"])).fetchone()[0]

            # Add junction entries to link source the source files used by an INF
            for source in e["SOURCES_USED"]:
                row = (id, "instanced_inf", inf_id, "source", source)
                db_cursor.execute(INSERT_JUNCTION_ROW, row)

            # Add junction entires to link libraries / components to the libraries they consume.
            for cls, instance in e["LIBRARIES_USED"]:
                if instance is None:
                    used_inf_id = None  # no library instance found for this library class
                else:
                    used_inf_id = db_cursor.execute(GET_ROW_ID, (id, instance, e["DSC"], cls)).fetchone()[0]

                row = (id, "instanced_inf", inf_id, "instanced_inf", used_inf_id)
                db_cursor.execute(INSERT_JUNCTION_ROW, row)

    def _build_inf_table(self, dscp: DscP):

        inf_entries = []
        for (inf, scope, overrides) in dscp.Components:
            logging.debug(f"Parsing Component: [{inf}]")
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
        lib_cls: str,
        component: str,
        library_dict: dict,
        override_dict: dict,
        scope: str,
        visited: list[str]
    ):
        """Recurses down all libraries starting from a single INF.

        Will immediately return if the INF has already been visited.
        """
        if inf is None:
            return []

        logging.debug(f"  Parsing Library: [{inf}]")
        visited.append(inf)
        library_instance_list = []
        library_class_list = []


        #
        # 0. Use the existing parser to parse the INF file. This parser parses an INF as an independent file
        #    and does not take into account the context of a DSC.
        #
        infp = self.inf(inf)

        #
        # 1. Convert all libraries to their actual instances for this component. This takes into account
        #    any overrides for this component
        #
        for lib in infp.get_libraries(self.arch):
            lib = lib.split(" ")[0]
            library_instance_list.append(self._lib_to_instance(lib.lower(), scope, library_dict, override_dict))
            library_class_list.append(lib)

        #
        # 2. Append all NULL library instances
        #
        for null_lib in override_dict["NULL"]:
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
        def to_posix(path):
            if path is None:
                return None
            return Path(path).as_posix()
        library_instance_list = list(map(to_posix, library_instance_list))

        # Return Paths as posix paths, which is Edk2 standard.
        to_return.append({
            "DSC": Path(self.dsc).name,
            "PATH": Path(inf).as_posix(),
            "GUID": infp.Dict.get("FILE_GUID", ""),
            "NAME": infp.Dict["BASE_NAME"],
            "LIBRARY_CLASS": lib_cls,
            "COMPONENT": Path(component).as_posix(),
            "MODULE_TYPE": infp.Dict["MODULE_TYPE"],
            "ARCH": scope.split(".")[0].upper(),
            "SOURCES_USED": list(map(lambda p: Path(p).as_posix(), infp.Sources)),
            "LIBRARIES_USED": list(zip(library_class_list, library_instance_list)),
            "PROTOCOLS_USED": [],  # TODO
            "GUIDS_USED": [],  # TODO
            "PPIS_USED": [],  # TODO
            "PCDS_USED": infp.PcdsUsed,
        })
        return to_return

    def _lib_to_instance(self, library_class_name, scope, library_dict, override_dict):
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
                return library_instance
        return None
