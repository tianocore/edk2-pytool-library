# @file plugin_setup.py
# Code to help parse DEC file
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier(self): BSD-2-Clause-Patent
##

## TODO: This file will handle dispatching to plugins handling section data

from cper_section_data_parser import SECTION_PARSER_PLUGIN

class PLUGIN_SETUP(object):

    def __init__(self,SECTION_PARSER_PLUGIN):
        pass

    def LoadPlugins(self):
        pass

    def CheckPluginsForGuid(self,guid):
        pass

    def ApplyPlugin(self,data):
        pass