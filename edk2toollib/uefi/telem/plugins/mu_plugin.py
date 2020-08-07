# @file mu_plugin.py
# Code to help parse cper header
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

from ..cper_section_data_parser import SECTION_PARSER_PLUGIN

class MU_SECTION_DATA_PARSER(SECTION_PARSER_PLUGIN):

    def __init__(self):
        pass

    def CanParse(self,guid):
        return True

    def Parse(self,data):
        pass