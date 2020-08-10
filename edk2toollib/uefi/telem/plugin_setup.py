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
        self.FoundPlugin = None

    def LoadPlugins(self):
        subclasslist = SECTION_PARSER_PLUGIN.__subclasses__()
        
        for cl in subclasslist:
            self.SubclassList.append(cl())

    def CheckPluginsForGuid(self,guid):
        for p in self.SubclassList:
            print("Checking if " + p.__str__() + " can parse the data...")
            if p.CanParse(guid):
                print(p.__str__()  + " can parse the data")
                self.FoundPlugin = p
                return True
            else:
                print(p.__str__() + " cannot parse the data")
        
        return False

    def ApplyPlugin(self,data):
        try:
            self.FoundPlugin.Parse(data)   
        except:
            print("Unable to apply plugin " + type(self.FoundPlugin).__name__  + " on data!")