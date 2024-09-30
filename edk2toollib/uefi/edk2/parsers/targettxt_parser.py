# @file targettxt_parser.py
# Code to help parse Edk2 Conf/Target.txt file
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Code to help parse Edk2 Conf/Target.txt file."""

import os

from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser


class TargetTxtParser(HashFileParser):
    """Parser for the Edk2 Conf/Target.txt file.

    Attributes:
        Parsed (bool): Whether the object has parsed a file or not
        Lines (list): Ordered list of each line in the file
        Dict (dict): Key / Value pair of all lines that contain a `=` in them (key=value)
        Path (str): path to Target.txt file
    """

    def __init__(self) -> "TargetTxtParser":
        """Inits an empty parser."""
        HashFileParser.__init__(self, "TargetTxtParser")
        self.Lines = []
        self.Parsed = False
        self.Dict = {}
        self.Path = ""

    def ParseFile(self, filepath: str) -> None:
        """Parses the file provided."""
        self.Logger.debug("Parsing file: %s" % filepath)
        if not os.path.isabs(filepath):
            fp = self.FindPath(filepath)
        else:
            fp = filepath
        self.Path = fp
        f = open(fp, "r")
        self.Lines = f.readlines()
        f.close()

        for line in self.Lines:
            sline = self.StripComment(line)

            if sline is None or len(sline) < 1:
                continue

            if sline.count("=") == 1:
                tokens = sline.split("=", 1)
                self.Dict[tokens[0].strip()] = tokens[1].strip()
                self.Logger.debug("Key,values found:  %s = %s" % (tokens[0].strip(), tokens[1].strip()))
                continue

        self.Parsed = True
