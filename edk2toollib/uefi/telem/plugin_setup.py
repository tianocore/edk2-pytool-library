# @file plugin_setup.py
# Code to help parse DEC file
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier(self): BSD-2-Clause-Patent
##

## TODO: This file will handle dispatching to plugins handling section data

from cper_section_data_parser import SECTION_PARSER_PLUGIN
from plugins import *

class PLUGIN_SETUP(object):

    def __init__(self):
        self.SubclassList = []
        self.LoadPlugins()

    def LoadPlugins(self):
        subclasslist = SECTION_PARSER_PLUGIN.__subclasses__()
        
        for cl in subclasslist:
            self.SubclassList.append(cl())

    def CheckPluginsForGuid(self,guid):
        for p in self.SubclassList:
            if p.CanParse(guid):
                print(type(p).__name__ + " can parse the guid")

    def ApplyPlugin(self,data):
        pass