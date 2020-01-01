# @file fdf_parser.py
# Code to help parse EDK2 Fdf files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.limited_fdf_parser import LimitedFdfParser
from edk2toollib.uefi.edk2.build_objects.fdf import *
from edk2toollib.uefi.edk2.build_objects.dsc import definition
from edk2toollib.uefi.edk2.parsers.dsc_parser import SectionProcessor
from edk2toollib.uefi.edk2.parsers.dsc_parser import AccurateParser
import os


class FdfParser(LimitedFdfParser, AccurateParser):

    def __init__(self):
        LimitedFdfParser.__init__(self)
        self.SourcedLines = []

    def ParseFile(self, filepath):
        if self.Parsed != False:  # make sure we haven't already parsed the file
            return
        super().ParseFile(filepath)
        self.fdf = fdf(filepath)
        self.ResetLineIterator()
        callbacks = self.GetCallbacks()
        print(self.Lines)
        processors = []
        while not self._IsAtEndOfLines:
            success = False
            for proc in processors:
                if proc.AttemptToProcessSection():
                    success = True
                    break
            if not success and not self._IsAtEndOfLines:
                line, source = self._ConsumeNextLine()
                self.Logger.warning(f"FDF Unknown line {line} @{source}")

        self.Parsed = True

        return self.fdf