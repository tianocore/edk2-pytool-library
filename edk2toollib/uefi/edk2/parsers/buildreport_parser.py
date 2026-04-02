# @file buildreport_parser.py
# Code to help parse an EDk2 Build Report
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Code to help parse an Edk2 Build Report."""

import logging
import os
from enum import Enum
from typing import Optional
from pathlib import Path

import edk2toollib.uefi.edk2.path_utilities as pu


class ModuleSummary(object):
    """Object to represent a module within the Build Report.

    Attributes:
        Guid (str): Module Guid
        Name (str): Module name
        InfPath (str): Path to INF
        Type (str): Module type
        PCDs (dict): Dict containing PCDs
        Libraries (dict): Dict containing libraries
        Depex (str): module depex
        WorkspacePath (str): workspace root
        PackagePathList (list): list of package paths
        FvName (str): Name of Fv
    """

    def __init__(self, content: str, ws: str, packagepatahlist: list, pathconverter: pu.Edk2Path) -> "ModuleSummary":
        """Inits an empty Module Summary Object."""
        self._RawContent = content
        self.Guid = ""
        self.Name = ""
        self.InfPath = ""
        self.Type = ""
        self.PCDs = {}
        self.Libraries = {}
        self.NullLibraryCount = 0
        self.Depex = ""
        self.WorkspacePath = ws
        self.PackagePathList = packagepatahlist
        self.FvName = None
        self.pathConverter = pathconverter

    def Parse(self) -> None:
        """Parses the Module summary object."""
        inPcdSection = False
        inLibSection = False
        inDepSection = False
        inOverallDepex = False
        nextLineSection = False
        tokenspace = ""

        i = 0
        try:
            while i < len(self._RawContent):
                line = self._RawContent[i].strip()

                # parse start and end
                if (
                    line
                    == ">----------------------------------------------------------------------------------------------------------------------<"
                ):  # noqa: E501
                    nextLineSection = True

                elif (
                    line
                    == "<---------------------------------------------------------------------------------------------------------------------->"
                ):  # noqa: E501
                    inPcdSection = False
                    inLibSection = False
                    inDepSection = False
                    nextLineSection = False

                # parse section header
                elif nextLineSection:
                    nextLineSection = False
                    if line == "Library":
                        inLibSection = True
                        i += 1  # add additional line to skip the dashed line

                    elif line == "PCD":
                        inPcdSection = True
                        i += 1  # add additional line to skip the dashed line

                    elif line == "Final Dependency Expression (DEPEX) Instructions":
                        inDepSection = True
                        i += 1  # add additional line to skip the dashed line
                    elif line == "Dependency Expression (DEPEX) from INF":
                        # For some reason, "Final Dependency Expression (DEPEX) Instructions" does not exist
                        # For all modules, so we need to check for this as well.
                        inDepSection = True
                        inOverallDepex = True
                    else:
                        logging.debug("Unsupported Section: " + line)
                        inPcdSection = False
                        inLibSection = False
                        inDepSection = False

                # Normal section parsing
                else:
                    if inLibSection:
                        logging.debug("InLibSection: %s" % line)
                        # get the whole statement library class statement
                        templine = line.strip()
                        while "}" not in templine:
                            i += 1
                            templine += self._RawContent[i].strip()

                        # have good complete line with no whitespace/newline chars
                        # first is the library instance INF
                        # second is the library class

                        lib_class = templine.partition("{")[2].partition("}")[0].partition(":")[0].strip()
                        lib_instance = templine.partition("{")[0].strip()

                        if lib_class.strip().lower() == "null":
                            lib_class += str(self.NullLibraryCount)
                            self.NullLibraryCount += 1

                        # Take absolute path and convert to EDK build path
                        RelativePath = self.pathConverter.GetEdk2RelativePathFromAbsolutePath(lib_instance)
                        if RelativePath is not None:
                            self.Libraries[lib_class] = RelativePath
                        else:
                            self.Libraries[lib_class] = lib_instance
                        i += 1
                        continue

                    elif inPcdSection:
                        # this is the namespace token line
                        if len(line.split()) == 1:
                            tokenspace = line

                        # this is the main line of the PCD value
                        elif line.count("=") == 1 and line.count(":") == 1:
                            while (line.count('"') % 2) != 0:
                                i += 1
                                line += " " + self._RawContent[i].rstrip()
                            while line.count("{") != line.count("}"):
                                i += 1
                                line += " " + self._RawContent[i].rstrip()

                            token = line.partition("=")[2]
                            if line.partition(":")[0].split() == []:
                                token2 = ""
                            else:
                                token2 = line.partition(":")[0].split()[-1]
                            self.PCDs[tokenspace + "." + token2] = token.strip()

                        # this is the secondary lines of PCD values showing Defaults
                        elif line.count(":") == 0 and line.count("=") == 1:
                            while (line.count('"') % 2) != 0:
                                i += 1
                                line += self._RawContent[i].rstrip()

                    elif inDepSection:
                        if line == "Dependency Expression (DEPEX) from INF":
                            inOverallDepex = True
                        elif line.startswith("-----"):
                            inOverallDepex = False

                        elif inOverallDepex:
                            self.Depex += " " + line

                    else:
                        # not in section...Must be header section
                        line_partitioned = line.partition(":")
                        if line_partitioned[2] == "":
                            pass  # not a name: value pair
                        else:
                            key = line_partitioned[0].strip().lower()
                            value = line_partitioned[2].strip()
                            if key == "module name":
                                logging.debug("Parsing Mod: %s" % value)
                                self.Name = value
                            elif key == "module inf path":
                                while ".inf" not in value.lower():
                                    i += 1
                                    value += self._RawContent[i].strip()
                                # Normalize separators then immediately convert to
                                # EDK2-relative path so InfPath is always relative when
                                # possible. This ensures exact-match in FindComponentByInfPath
                                # works correctly, including for extdep (external dependency)
                                # paths that may not be re-resolvable at match time.
                                abs_inf = value.replace("\\", "/")
                                if os.path.isabs(abs_inf):
                                    rel_inf = self.pathConverter.GetEdk2RelativePathFromAbsolutePath(abs_inf)
                                    self.InfPath = rel_inf if rel_inf is not None else abs_inf
                                else:
                                    self.InfPath = abs_inf
                            elif key == "file guid":
                                self.Guid = value
                            elif key == "driver type":
                                value = value.strip()
                                self.Type = value[value.index("(") + 1 : -1]

                i += 1
        except Exception:
            logging.debug("Exception in Parsing: %d" % i)
            raise


class BuildReport(object):
    """An object representing a parsed Build Report with capability to parse.

    Attributes:
        PlatformName (str): name
        DscPath (str): Path to DSC
        FdfPath (str): Path to FDF
        BuildOutputDir (str): Path to Build Output
        ReportFile (str): Path to Build Report
        Modules (dict): dict containing ModuleSummary type
        Workspace (str): Workspace root
        PackagesPathList (list): List of package paths
        ProtectedWords (dict): Dict of protected words
        PathConverter (Edk2Path): path utilities
    """

    class RegionTypes(Enum):
        """Enum for different Region Types."""

        PCD = "PCD"
        FD = "FD"
        MODULE = "MODULE"
        UNKNOWN = "UNKNOWN"

    def __init__(self, filepath: str, ws: str, packagepathcsv: str, protectedWordsDict: dict) -> "RegionTypes":
        """Inits an empty BuildReport object."""
        self.PlatformName = ""
        self.DscPath = ""
        self.FdfPath = ""
        self.BuildOutputDir = ""
        self.ReportFile = filepath
        self.Modules = {}  # fill this in with objects of ModuleSummary type
        self._ReportContents = ""
        self._Regions = []  # fill this in with tuple (type, start, end)
        self.Workspace = ws  # needs to contain the trailing slash
        self.PackagePathList = []
        for a in packagepathcsv.split(","):
            a = a.strip()
            if len(a) > 0:
                self.PackagePathList.append(a)
        self.ProtectedWords = protectedWordsDict
        self.PathConverter = pu.Edk2Path(self.Workspace, self.PackagePathList)

    #
    # do region level parsing
    # to get the layout, lists, and dictionaries setup.
    #
    def BasicParse(self) -> None:
        """Performs region level parsing.

        Gets the layout, lists, and dictionaries setup.
        """
        if not os.path.isfile(self.ReportFile):
            raise Exception("Report File path invalid!")

        # read report
        f = open(self.ReportFile, "r")
        self._ReportContents = [x.strip() for x in f.readlines()]
        f.close()
        #
        # replace protected words
        #
        for k, v in self.ProtectedWords.items():
            self._ReportContents = [x.replace(k, v) for x in self._ReportContents]

        logging.debug("Report File is: %s" % self.ReportFile)
        logging.debug("Input report had %d lines of content" % len(self._ReportContents))

        #
        # parse thru and find the regions and basic info at top
        # this is a little hacky in that internal operations could
        # fail but it doesn't seem critical
        #
        linenum = self._GetNextRegionStart(0)
        while linenum is not None:
            start = linenum
            end = self._GetEndOfRegion(start)
            type = self._GetRegionType(start)
            self._Regions.append((type, start, end))
            linenum = self._GetNextRegionStart(linenum)
            logging.debug("Found a region of type: %s start: %d end: %d" % (type, start, end))

        #
        # Parse the basic header of the report.
        # we do it after parsing region because we
        # can limit scope to 0 - first start
        #
        for n in range(self._Regions[0][1]):  # loop thru from 0 to start of first region
            line = self._ReportContents[n].strip()
            line_partitioned = line.partition(":")
            if line_partitioned[2] == "":
                continue

            key = line_partitioned[0].strip().lower()
            value = line_partitioned[2].strip()

            if key == "platform name":
                self.PlatformName = value
            elif key == "platform dsc path":
                self.DscPath = value
            elif key == "output path":
                self.BuildOutputDir = value

        #
        # now for each module summary
        # parse it
        for r in self._Regions:
            if r[0] == BuildReport.RegionTypes.MODULE:
                mod = ModuleSummary(
                    self._ReportContents[r[1] : r[2]], self.Workspace, self.PackagePathList, self.PathConverter
                )
                mod.Parse()
                self.Modules[mod.Guid] = mod

        # now that all modules are parsed lets parse the FD region so we can get the FV name for each module
        for r in self._Regions:
            # if FD region parse out all INFs in the all of the flash
            if r[0] == BuildReport.RegionTypes.FD:
                self._ParseFdRegionForModules(self._ReportContents[r[1] : r[2]])

    def FindComponentByInfPath(self, InfPath: str) -> Optional["ModuleSummary"]:
        """Attempts to find the Component the Inf is apart of.
           Convert absolute search path to an edk2-relative path first.
           Normalize separators and case for exact equality match.
           If no exact match, allow a trailing-path-components (suffix) match,
           but only return it when it is unambiguous (single best match).

        Args:
            InfPath: Inf Path

        Returns:
            (ModuleSummary): Module if found
            (None): If not found
        """
        if not InfPath:
            return None

        # Try to convert absolute search path to an edk2-relative path
        search_path = InfPath
        if os.path.isabs(search_path):
            try:
                rel = self.PathConverter.GetEdk2RelativePathFromAbsolutePath(search_path)
                if rel is not None:
                    search_path = rel
                    logging.debug("FindComponentByInfPath: resolved absolute search path to '%s'" % search_path)
            except Exception:
                pass

        # Normalize using pathlib
        search_norm = Path(search_path).as_posix().lower()
        search_parts = [p for p in Path(search_norm).parts if p not in ("", "/")]

        if not search_parts:
            return None

        candidates = []
        search_len = len(search_parts)

        for v in self.Modules.values():
            if not v.InfPath:
                # Module was parsed but InfPath was not recorded; skip.
                continue

            # Resolve the stored module InfPath to EDK2-relative form if it is
            # still absolute.  After the ModuleSummary.Parse() fix, InfPath
            # should already be relative for most modules; this guard handles
            # any edge-cases (e.g. modules added programmatically) where it
            # may still be absolute.
            module_inf = v.InfPath
            if os.path.isabs(module_inf):
                try:
                    rel = self.PathConverter.GetEdk2RelativePathFromAbsolutePath(module_inf)
                    if rel is not None:
                        module_inf = rel
                except Exception:
                    pass  # Keep absolute form; suffix match may still succeed.

            # Normalize the module path with the same rules as the search path.
            mod_norm = Path(module_inf).as_posix().lower()
            mod_parts = [p for p in Path(mod_norm).parts if p not in ("", "/")]

            # Check for exact match
            if mod_norm == search_norm:
                logging.debug("Found Module by exact InfPath: %s == %s" % (InfPath, module_inf))
                return v  # Return immediately on exact match

            # Check whether the last N components of the module path equal all
            # N components of the search path.  Record the number of extra
            # leading components in the module path so we can prefer the
            # closest (shortest extra prefix) match later.
            if len(mod_parts) >= search_len and mod_parts[-search_len:] == search_parts:
                extra = len(mod_parts) - search_len  # smaller is better (closer match)
                candidates.append((extra, v, mod_norm))

        if not candidates:
            logging.error("Failed to find Module by InfPath %s" % InfPath)
            return None

        # Sort by ascending extra-component count so the closest match is first.
        candidates.sort(key=lambda t: t[0])
        best_extra = candidates[0][0]
        # Collect all candidates that tie for the best (smallest extra) score.
        best_candidates = [c for c in candidates if c[0] == best_extra]

        if len(best_candidates) == 1:
            # Unambiguous best suffix match — safe to return.
            _, best_module, best_mod_norm = best_candidates[0]
            logging.debug("Found Module by trailing InfPath match: %s in %s" % (InfPath, best_mod_norm))
            return best_module

        ambiguous_list = [c[2] for c in best_candidates]
        logging.error(
            "Ambiguous INF match for %s; candidates: %s. Not selecting to avoid false positive."
            % (InfPath, ", ".join(ambiguous_list))
        )
        return None

    def _ParseFdRegionForModules(self, rawcontents: str) -> None:
        FvName = None
        index = 0
        WorkspaceAndPPList = [self.Workspace]
        WorkspaceAndPPList.extend(self.PackagePathList)

        while index < len(rawcontents):
            a = rawcontents[index]
            tokens = a.split()
            if a.startswith("0x") and (len(tokens) == 3) and (a.count("(") == 1):
                if ".inf" not in a.lower() or (a.count("(") != a.count(")")):
                    a = a + rawcontents[index + 1].strip()
                    index += 1
                    tokens = a.split()

                i = a.split()[2].strip().strip("()")

                logging.debug("Found INF in FV Region: " + i)

                # Take absolute path and convert to EDK build path
                RelativePath = self.PathConverter.GetEdk2RelativePathFromAbsolutePath(i)
                if RelativePath is not None:
                    comp = self.FindComponentByInfPath(RelativePath)
                    if comp is not None:
                        comp.FvName = FvName
                    else:
                        logging.error("Failed to find component for INF path %a" % RelativePath)

            elif a.startswith("Fv Name:"):
                # Fv Name:            FV_DXE (99.5% Full)
                FvName = a.partition(":")[2].strip().split()[0]
                logging.debug("Found FvName. RAW: %s  Name: %s" % (a, FvName))
            else:
                logging.debug("ignored line in FD parsing: %s" % a)
            index += 1

        return

    #
    # Get the start of region
    #
    def _GetNextRegionStart(self, number: int) -> Optional[int]:
        lineNumber = number
        while lineNumber < len(self._ReportContents):
            if (
                self._ReportContents[lineNumber]
                == ">======================================================================================================================<"
            ):  # noqa: E501
                return lineNumber + 1
            lineNumber += 1
        logging.debug("Failed to find a Start Next Region after lineNumber: %d" % number)
        # didn't find new region
        return None

    #
    # Get the end of region
    #
    def _GetEndOfRegion(self, number: int) -> Optional[int]:
        lineNumber = number
        while lineNumber < len(self._ReportContents):
            if (
                self._ReportContents[lineNumber]
                == "<======================================================================================================================>"
            ):  # noqa: E501
                return lineNumber - 1
            lineNumber += 1

        logging.debug("Failed to find a End Region after lineNumber: %d" % number)
        # didn't find new region
        return None

    def _GetRegionType(self, lineNumber: int) -> "BuildReport.RegionTypes":
        line = self._ReportContents[lineNumber].strip()
        if line == "Firmware Device (FD)":
            return BuildReport.RegionTypes.FD
        elif line == "Platform Configuration Database Report":
            return BuildReport.RegionTypes.PCD
        elif line == "Module Summary":
            return BuildReport.RegionTypes.MODULE
        else:
            return BuildReport.RegionTypes.UNKNOWN
