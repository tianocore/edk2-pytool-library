# @file fdf_parser.py
# Code to help parse EDK2 Fdf files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.limited_fdf_parser import LimitedFdfParser
from edk2toollib.uefi.edk2.build_objects.fdf import *
import os

class FdfParser(LimitedFdfParser):

    def __init__(self):
        super().__init__()

    def ParseFile(self, filepath):
        self.fdf = fdf()
        return self.fdf