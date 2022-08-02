# @file targettxt_parser.py
# Code to help parse Edk2 Conf/Target.txt file
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser
import os


class TargetTxtParser(HashFileParser):

    def __init__(self):
        HashFileParser.__init__(self, 'TargetTxtParser')
        self.Lines = []
        self.Parsed = False
        self.Dict = {}
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

        for line in self.Lines:
            sline = self.StripComment(line)

            if (sline is None or len(sline) < 1):
                continue

            if sline.count("=") == 1:
                tokens = sline.split('=', 1)
                self.Dict[tokens[0].strip()] = tokens[1].strip()
                self.Logger.debug("Key,values found:  %s = %s" % (tokens[0].strip(), tokens[1].strip()))
                continue

        self.Parsed = True
