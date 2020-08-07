# @file mu_plugin.py
# Parser for MU telemetry
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import sys
sys.path.append('../..')
from cper_section_data_parser import SECTION_PARSER_PLUGIN

class MU_SECTION_DATA_PARSER(SECTION_PARSER_PLUGIN):

    def __init__(self):
        pass

    def CanParse(self,guid):
        return True

    def Parse(self,data):
        pass