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
    def __init__(self, content, ws, packagepatahlist, pathconverter):
        """Inits an empty Module Summary Object."""
        self._RawContent = content
        self.Guid = ""
        self.Name = ""
        self.InfPath = ""
        self.Type = ""
        self.PCDs = {}
        self.Libraries = {}
        self.Depex = ""
        self.WorkspacePath = ws
        self.PackagePathList = packagepatahlist
        self.FvName = None
        self.pathConverter = pathconverter

    def Parse(self):
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
                if line == ">----------------------------------------------------------------------------------------------------------------------<":      # noqa: E501
                    nextLineSection = True

                elif line == "<---------------------------------------------------------------------------------------------------------------------->":    # noqa: E501
                    inPcdSection = False
                    inLibSection = False
                    inDepSection = False
                    nextLineSection = False

                # parse section header
                elif (nextLineSection):
                    nextLineSection = False
                    if (line == "Library"):
                        inLibSection = True
                        i += 1  # add additional line to skip the dashed line

                    elif (line == "PCD"):
                        inPcdSection = True
                        i += 1  # add additional line to skip the dashed line

                    elif (line == "Final Dependency Expression (DEPEX) Instructions"):
                        inDepSection = True
                        i += 1  # add additional line to skip the dashed line
                    elif (line == "Dependency Expression (DEPEX) from INF"):
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
                    if (inLibSection):
                        logging.debug("InLibSection: %s" % line)
                        # get the whole statement library class statement
                        templine = line.strip()
                        while ('}' not in templine):
                            i += 1
                            templine += self._RawContent[i].strip()

                        # have good complete line with no whitespace/newline chars
                        # first is the library instance INF
                        # second is the library class

                        lib_class = templine.partition('{')[2].partition('}')[0].partition(':')[0].strip()
                        lib_instance = templine.partition('{')[0].strip()

                        # Take absolute path and convert to EDK build path
                        RelativePath = self.pathConverter.GetEdk2RelativePathFromAbsolutePath(lib_instance)
                        if (RelativePath is not None):
                            self.Libraries[lib_class] = RelativePath
                        else:
                            self.Libraries[lib_class] = lib_instance
                        i += 1
                        continue

                    elif (inPcdSection):
                        # this is the namespace token line
                        if (len(line.split()) == 1):
                            tokenspace = line

                        # this is the main line of the PCD value
                        elif (line.count("=") == 1 and line.count(":") == 1):
                            while (line.count("\"") % 2) != 0:
                                i += 1
                                line += " " + self._RawContent[i].rstrip()
                            while (line.count('{') != line.count('}')):
                                i += 1
                                line += " " + self._RawContent[i].rstrip()

                            token = line.partition('=')[2]
                            if (line.partition(':')[0].split() == []):
                                token2 = ""
                            else:
                                token2 = line.partition(':')[0].split()[-1]
                            self.PCDs[tokenspace + "." + token2] = token.strip()

                        # this is the secondary lines of PCD values showing Defaults
                        elif line.count(":") == 0 and line.count("=") == 1:
                            while (line.count("\"") % 2) != 0:
                                i += 1
                                line += self._RawContent[i].rstrip()

                    elif (inDepSection):
                        if line == "Dependency Expression (DEPEX) from INF":
                            inOverallDepex = True
                        elif line.startswith("-----"):
                            inOverallDepex = False

                        elif inOverallDepex:
                            self.Depex += " " + line

                    else:
                        # not in section...Must be header section
                        line_partitioned = line.partition(':')
                        if (line_partitioned[2] == ""):
                            pass  # not a name: value pair
                        else:
                            key = line_partitioned[0].strip().lower()
                            value = line_partitioned[2].strip()
                            if (key == "module name"):
                                logging.debug("Parsing Mod: %s" % value)
                                self.Name = value
                            elif (key == "module inf path"):
                                while (".inf" not in value.lower()):
                                    i += 1
                                    value += self._RawContent[i].strip()
                                self.InfPath = value.replace("\\", "/")
                            elif (key == "file guid"):
                                self.Guid = value
                            elif (key == "driver type"):
                                value = value.strip()
                                self.Type = value[value.index('(') + 1:-1]

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
        PCD = 'PCD'
        FD = 'FD'
        MODULE = 'MODULE'
        UNKNOWN = 'UNKNOWN'

    def __init__(self, filepath, ws, packagepathcsv, protectedWordsDict):
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
            if (len(a) > 0):
                self.PackagePathList.append(a)
        self.ProtectedWords = protectedWordsDict
        self.PathConverter = pu.Edk2Path(self.Workspace, self.PackagePathList)

    #
    # do region level parsing
    # to get the layout, lists, and dictionaries setup.
    #
    def BasicParse(self):
        """Performs region level parsing.

        Gets the layout, lists, and dictionaries setup.
        """
        if (not os.path.isfile(self.ReportFile)):
            raise Exception("Report File path invalid!")

        # read report
        f = open(self.ReportFile, "r")
        self._ReportContents = [x.strip() for x in f.readlines()]
        f.close()
        #
        # replace protected words
        #
        for (k, v) in self.ProtectedWords.items():
            self._ReportContents = [x.replace(k, v) for x in self._ReportContents]

        logging.debug("Report File is: %s" % self.ReportFile)
        logging.debug("Input report had %d lines of content" % len(self._ReportContents))

        #
        # parse thru and find the regions and basic info at top
        # this is a little hacky in that internal operations could
        # fail but it doesn't seem critical
        #
        linenum = self._GetNextRegionStart(0)
        while (linenum is not None):
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
            line_partitioned = line.partition(':')
            if (line_partitioned[2] == ""):
                continue

            key = line_partitioned[0].strip().lower()
            value = line_partitioned[2].strip()

            if (key == "platform name"):
                self.PlatformName = value
            elif (key == "platform dsc path"):
                self.DscPath = value
            elif (key == "output path"):
                self.BuildOutputDir = value

        #
        # now for each module summary
        # parse it
        for r in self._Regions:
            if (r[0] == BuildReport.RegionTypes.MODULE):
                mod = ModuleSummary(self._ReportContents[r[1]:r[2]],
                                    self.Workspace, self.PackagePathList,
                                    self.PathConverter)
                mod.Parse()
                self.Modules[mod.Guid] = mod

        # now that all modules are parsed lets parse the FD region so we can get the FV name for each module
        for r in self._Regions:
            # if FD region parse out all INFs in the all of the flash
            if (r[0] == BuildReport.RegionTypes.FD):
                self._ParseFdRegionForModules(self._ReportContents[r[1]:r[2]])

    def FindComponentByInfPath(self, InfPath):
        """Attempts to find the Component the Inf is apart of.

        Args:
            InfPath (str): Inf Path

        Returns:
            (ModuleSummary): Module if found
            (None): If not found
        """
        for (k, v) in self.Modules.items():
            if (v.InfPath.lower() == InfPath.lower()):
                logging.debug("Found Module by InfPath: %s" % InfPath)
                return v

        logging.error("Failed to find Module by InfPath %s" % InfPath)
        return None

    def _ParseFdRegionForModules(self, rawcontents):
        FvName = None
        index = 0
        WorkspaceAndPPList = [self.Workspace]
        WorkspaceAndPPList.extend(self.PackagePathList)

        while index < len(rawcontents):
            a = rawcontents[index]
            tokens = a.split()
            if a.startswith("0x") and (len(tokens) == 3) and (a.count('(') == 1):
                if ".inf" not in a.lower() or (a.count('(') != a.count(")")):
                    a = a + rawcontents[index + 1].strip()
                    index += 1
                    tokens = a.split()

                i = a.split()[2].strip().strip('()')

                logging.debug("Found INF in FV Region: " + i)

                # Take absolute path and convert to EDK build path
                RelativePath = self.PathConverter.GetEdk2RelativePathFromAbsolutePath(i)
                if (RelativePath is not None):
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
    def _GetNextRegionStart(self, number):
        lineNumber = number
        while (lineNumber < len(self._ReportContents)):
            if self._ReportContents[lineNumber] == ">======================================================================================================================<":  # noqa: E501
                return lineNumber + 1
            lineNumber += 1
        logging.debug("Failed to find a Start Next Region after lineNumber: %d" % number)
        # didn't find new region
        return None

    #
    # Get the end of region
    #
    def _GetEndOfRegion(self, number):
        lineNumber = number
        while (lineNumber < len(self._ReportContents)):
            if self._ReportContents[lineNumber] == "<======================================================================================================================>":  # noqa: E501
                return lineNumber - 1
            lineNumber += 1

        logging.debug("Failed to find a End Region after lineNumber: %d" % number)
        # didn't find new region
        return None

    def _GetRegionType(self, lineNumber):
        line = self._ReportContents[lineNumber].strip()
        if (line == "Firmware Device (FD)"):
            return BuildReport.RegionTypes.FD
        elif (line == "Platform Configuration Database Report"):
            return BuildReport.RegionTypes.PCD
        elif (line == "Module Summary"):
            return BuildReport.RegionTypes.MODULE
        else:
            return BuildReport.RegionTypes.UNKNOWN
