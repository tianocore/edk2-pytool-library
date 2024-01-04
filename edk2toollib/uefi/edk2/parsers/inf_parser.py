# @file inf_parser.py
# Code to help parse EDK2 INF files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Code to help parse EDK2 INF files."""
import os
import re

from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser

AllPhases = ["SEC", "PEIM", "PEI_CORE", "DXE_DRIVER", "DXE_CORE", "DXE_RUNTIME_DRIVER", "UEFI_DRIVER",
             "SMM_CORE", "DXE_SMM_DRIVER", "UEFI_APPLICATION", "MM_STANDALONE", "MM_CORE_STANDALONE",
             "HOST_APPLICATION",]


class InfParser(HashFileParser):
    """Object representing a parsed INF with capabilities to parse an INF.

    Attributes:
        Parsed (bool): Whether the object contains a parsed INF
        Lines (list[str]): ordered list of all lines in the INF
        Dict (dict): Key / Value pairs found in the INF.
        LibraryClass (str): library class of the INF
        SupportedPhases (list[str]): list of supported phases (i.e. "SEC", "PEIM", etc.)
        PackagesUsed (list[str]): list of packages used
        LibrariesUsed (list[str]): list of libraries used
        ProtocolsUsed (list[str]): list of protocols used
        GuidsUsed (list[str]): list of guids used
        PpisUsed (list[str]): list of Ppis used
        PcdsUsed (list[str]): list of Pcds used
        Sources (list[str]): list of source files used
        Binaries (list[str]): list of binaries used
        Path (str): Path to the INF file

    NOTE: Key / Value pairs determined by lines that contain a single =
    """
    SECTION_REGEX = re.compile(r"\[(.*)\]")
    SECTION_LIBRARY = re.compile(r'libraryclasses(?:\.([^,.\]]+))?[,.\]]', re.IGNORECASE)
    SECTION_SOURCE = re.compile(r'sources(?:\.([^,.\]]+))?[,.\]]', re.IGNORECASE)

    def __init__(self) -> 'InfParser':
        """Inits an empty parser."""
        HashFileParser.__init__(self, 'ModuleInfParser')
        self.Lines = []
        self.Parsed = False
        self.Dict = {}
        self.LibraryClass = ""
        self.SupportedPhases = []
        self.PackagesUsed = []
        self.LibrariesUsed = []
        self.ScopedLibraryDict = {}
        self.ScopedSourceDict = {}
        self.ProtocolsUsed = []
        self.GuidsUsed = []
        self.PpisUsed = []
        self.PcdsUsed = []
        self.Sources = []
        self.Binaries = []
        self.Path = ""

    def get_libraries(self, arch_list: list[str]) -> list[str]:
        """Returns a list of libraries depending on the requested archs."""
        libraries = self.ScopedLibraryDict.get("common", []).copy()

        for arch in arch_list:
            libraries = libraries + self.ScopedLibraryDict.get(arch.lower(), []).copy()
        return list(set(libraries))

    def get_sources(self, arch_list: list[str]) -> list[str]:
        """Returns a list of sources depending on the requested archs."""
        sources = self.ScopedSourceDict.get("common", []).copy()

        for arch in arch_list:
            sources = sources + self.ScopedSourceDict.get(arch.lower(), []).copy()
        return list(set(sources))

    def ParseFile(self, filepath: str) -> None:
        """Parses the INF file provided."""
        self.Logger.debug("Parsing file: %s" % filepath)
        if (not os.path.isabs(filepath)):
            fp = self.FindPath(filepath)
        else:
            fp = filepath
        self.Path = fp
        f = open(fp, "r")
        self.Lines = f.readlines()
        f.close()
        InDefinesSection = False
        InPackagesSection = False
        InLibraryClassSection = False
        InProtocolsSection = False
        InGuidsSection = False
        InPpiSection = False
        InPcdSection = False
        InSourcesSection = False
        InBinariesSection = False

        for line in self.Lines:
            sline = self.StripComment(line)

            if (sline is None or len(sline) < 1):
                continue

            sline = self.ReplaceVariables(sline)

            if sline.strip().startswith("DEFINE"):
                tokens = sline.strip().replace("DEFINE", "").split('=', 1)
                self.LocalVars[tokens[0].strip()] = tokens[1].strip()
                self.Logger.info(f"Key,values found for local vars: {tokens[0].strip()}, {tokens[1].strip()}")
                continue

            elif InDefinesSection:
                if sline.strip()[0] == '[':
                    InDefinesSection = False
                else:
                    if sline.count("=") == 1:
                        tokens = sline.split('=', 1)
                        self.Dict[tokens[0].strip()] = tokens[1].strip()
                        #
                        # Parse Library class and phases in special manor
                        #
                        if (tokens[0].strip().lower() == "library_class"):
                            self.LibraryClass = tokens[1].partition("|")[0].strip()
                            self.Logger.debug("Library class found")
                            if (len(tokens[1].partition("|")[2].strip()) < 1):
                                self.SupportedPhases = AllPhases
                            elif (tokens[1].partition("|")[2].strip().lower() == "base"):
                                self.SupportedPhases = AllPhases
                            else:
                                self.SupportedPhases = tokens[1].partition("|")[2].strip().split()

                        self.Logger.debug("Key,values found:  %s = %s" % (tokens[0].strip(), tokens[1].strip()))

                        continue

            elif InPackagesSection:
                if sline.strip()[0] == '[':
                    InPackagesSection = False
                else:
                    self.PackagesUsed.append(sline.partition("|")[0].strip())
                    continue

            elif InLibraryClassSection:
                if sline.strip()[0] == '[':
                    InLibraryClassSection = False
                else:
                    self.LibrariesUsed.append(sline.partition("|")[0].strip())
                    continue

            elif InProtocolsSection:
                if sline.strip()[0] == '[':
                    InProtocolsSection = False
                else:
                    self.ProtocolsUsed.append(sline.partition("|")[0].strip())
                    continue

            elif InGuidsSection:
                if sline.strip()[0] == '[':
                    InGuidsSection = False
                else:
                    self.GuidsUsed.append(sline.partition("|")[0].strip())
                    continue

            elif InPcdSection:
                if sline.strip()[0] == '[':
                    InPcdSection = False
                else:
                    self.PcdsUsed.append(sline.partition("|")[0].strip())
                    continue

            elif InPpiSection:
                if sline.strip()[0] == '[':
                    InPpiSection = False
                else:
                    self.PpisUsed.append(sline.partition("|")[0].strip())
                    continue

            elif InSourcesSection:
                if sline.strip()[0] == '[':
                    InSourcesSection = False
                else:
                    self.Sources.append(sline.partition("|")[0].strip())
                    continue

            elif InBinariesSection:
                if sline.strip()[0] == '[':
                    InBinariesSection = False
                else:
                    self.Binaries.append(sline.partition("|")[0].strip())
                    continue

            # check for different sections
            if sline.strip().lower().startswith('[defines'):
                InDefinesSection = True

            elif sline.strip().lower().startswith('[packages'):
                InPackagesSection = True

            elif sline.strip().lower().startswith('[libraryclasses'):
                InLibraryClassSection = True

            elif sline.strip().lower().startswith('[protocols'):
                InProtocolsSection = True

            elif sline.strip().lower().startswith('[ppis'):
                InPpiSection = True

            elif sline.strip().lower().startswith('[guids'):
                InGuidsSection = True

            elif sline.strip().lower().startswith('[pcd') or \
                    sline.strip().lower().startswith('[patchpcd') or \
                    sline.strip().lower().startswith('[fixedpcd') or \
                    sline.strip().lower().startswith('[featurepcd'):
                InPcdSection = True

            elif sline.strip().lower().startswith('[sources'):
                InSourcesSection = True

            elif sline.strip().lower().startswith('[binaries'):
                InBinariesSection = True

        # Re-parse for scoped information
        # Hopefully eventually replace all of the above with this
        # logic
        current_section = ""
        arch_list = []

        for line in self.Lines:
            line = self.StripComment(line)

            if line.strip() == "":
                continue

            if line.strip().startswith("#"):
                continue

            if line.strip().startswith("DEFINE"):
                tokens = line.strip().replace("DEFINE", "").split('=', 1)
                self.LocalVars[tokens[0].strip()] = tokens[1].strip()
                self.Logger.info(f"Key,values found for local vars: {tokens[0].strip()}, {tokens[1].strip()}")
                continue

            line = self.ReplaceVariables(line)

            match = self.SECTION_LIBRARY.findall(line)
            if match:
                current_section = "LibraryClasses"
                arch_list = match
                continue
            match = self.SECTION_SOURCE.findall(line)
            if match:
                current_section = "Sources"
                arch_list = match
                continue

            # Catch all others
            match = self.SECTION_REGEX.match(line)
            if match:
                current_section = match.group(1)
                arch_list = []

            # Handle lines when we are in a library section
            if current_section == "LibraryClasses":
                for arch in arch_list:
                    arch = 'common' if arch == '' else arch.lower()
                    if arch in self.ScopedLibraryDict:
                        self.ScopedLibraryDict[arch].append(line.split()[0].strip())
                    else:
                        self.ScopedLibraryDict[arch] = [line.split()[0].strip()]

            # Handle lines when we are in a source section
            if current_section == "Sources":
                for arch in arch_list:
                    arch = 'common' if arch == '' else arch.lower()
                    src = line.split()[0].strip().rstrip('|')
                    if arch in self.ScopedSourceDict:
                        self.ScopedSourceDict[arch].append(src)
                    else:
                        self.ScopedSourceDict[arch] = [src]
        self.Parsed = True
