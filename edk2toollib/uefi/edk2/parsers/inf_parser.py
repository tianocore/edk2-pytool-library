# @file inf_parser.py
# Code to help parse EDK2 INF files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser
import os


AllPhases = ["SEC", "PEIM", "PEI_CORE", "DXE_DRIVER", "DXE_CORE", "DXE_RUNTIME_DRIVER", "UEFI_DRIVER",
             "SMM_CORE", "DXE_SMM_DRIVER", "UEFI_APPLICATION"]


class InfParser(HashFileParser):

    def __init__(self):
        HashFileParser.__init__(self, 'ModuleInfParser')
        self.Lines = []
        self.Parsed = False
        self.Dict = {}
        self.LibraryClass = ""
        self.SupportedPhases = []
        self.PackagesUsed = []
        self.LibrariesUsed = []
        self.ProtocolsUsed = []
        self.GuidsUsed = []
        self.PpisUsed = []
        self.PcdsUsed = []
        self.Sources = []
        self.Binaries = []
        self.Path = ""

    def ParseFile(self, filepath):
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

            if InDefinesSection:
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

        self.Parsed = True
