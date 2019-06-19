# @file dec_parser.py
# Code to help parse DEC file
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser
import os


class DecParser(HashFileParser):
    def __init__(self):
        HashFileParser.__init__(self, 'DecParser')
        self.Lines = []
        self.Parsed = False
        self.Dict = {}
        self.LibrariesUsed = []
        self.PPIsUsed = []
        self.ProtocolsUsed = []
        self.GuidsUsed = []
        self.PcdsUsed = []
        self.IncludesUsed = []
        self.Path = ""

    def ParseFile(self, filepath):
        self.Logger.debug("Parsing file: %s" % filepath)
        if(not os.path.isabs(filepath)):
            fp = self.FindPath(filepath)
        else:
            fp = filepath
        self.Path = fp

        f = open(fp, "r")
        self.Lines = f.readlines()
        f.close()
        InDefinesSection = False
        InLibraryClassSection = False
        InProtocolsSection = False
        InGuidsSection = False
        InPPISection = False
        InPcdSection = False
        InIncludesSection = False

        for line in self.Lines:
            sline = self.StripComment(line)

            if(sline is None or len(sline) < 1):
                continue

            if InDefinesSection:
                if sline.strip()[0] == '[':
                    InDefinesSection = False
                else:
                    if sline.count("=") == 1:
                        tokens = sline.split('=', 1)
                        self.Dict[tokens[0].strip()] = tokens[1].strip()
                        continue

            elif InLibraryClassSection:
                if sline.strip()[0] == '[':
                    InLibraryClassSection = False
                else:
                    t = sline.partition("|")
                    self.LibrariesUsed.append(t[0].strip())
                    continue

            elif InProtocolsSection:
                if sline.strip()[0] == '[':
                    InProtocolsSection = False
                else:
                    t = sline.partition("=")
                    self.ProtocolsUsed.append(t[0].strip())
                    continue

            elif InGuidsSection:
                if sline.strip()[0] == '[':
                    InGuidsSection = False
                else:
                    t = sline.partition("=")
                    self.GuidsUsed.append(t[0].strip())
                    continue

            elif InPcdSection:
                if sline.strip()[0] == '[':
                    InPcdSection = False
                else:
                    t = sline.partition("|")
                    self.PcdsUsed.append(t[0].strip())
                    continue

            elif InIncludesSection:
                if sline.strip()[0] == '[':
                    InIncludesSection = False
                else:
                    self.IncludesUsed.append(sline.strip())
                    continue

            elif InPPISection:
                if (sline.strip()[0] == '['):
                    InPPISection = False
                else:
                    t = sline.partition("=")
                    self.PPIsUsed.append(t[0].strip())
                    continue

            # check for different sections
            if sline.strip().lower().startswith('[defines'):
                InDefinesSection = True

            elif sline.strip().lower().startswith('[libraryclasses'):
                InLibraryClassSection = True

            elif sline.strip().lower().startswith('[protocols'):
                InProtocolsSection = True

            elif sline.strip().lower().startswith('[guids'):
                InGuidsSection = True

            elif sline.strip().lower().startswith('[ppis'):
                InPPISection = True

            elif sline.strip().lower().startswith('[pcd'):
                InPcdSection = True

            elif sline.strip().lower().startswith('[includes'):
                InIncludesSection = True

        self.Parsed = True
