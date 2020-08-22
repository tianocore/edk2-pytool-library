# @file a_test_plugin.py
# A testing plugin used to verify parsing
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import sys
import uuid

sys.path.append('../..')
from cper_section_data import SECTION_PARSER_PLUGIN

class EXAMPLE_PLUGIN(SECTION_PARSER_PLUGIN):

    def __init__(self):
        pass
    
    ##
    # Returns string representation of this parser
    ##
    def __str__(self) -> str:
        return "EXAMPLE PLUGIN"

    ##
    # True if this parser recognizes the input guid
    ##
    def CanParse(self,guid:uuid) -> bool:
        return False

    ##
    # Returns a string representation of the data passed in. It is assumed that
    # if this call runs, you are recieving section data you recognize
    ##
    def Parse(self,data:str) -> str:
        return ""