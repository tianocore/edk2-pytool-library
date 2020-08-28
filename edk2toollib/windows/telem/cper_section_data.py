# @file cper_section_data.py
# Base class for all parsing types
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import uuid

class SECTION_PARSER_PLUGIN(object):

    ##
    # Returns string representation of this parser
    ##
    def __str__(self) -> str:
        return "UNNAMED PLUGIN"

    ##
    # True if this parser recognizes the input guid
    ##
    def CanParse(self,guid:uuid) -> bool:
        raise NotImplementedError

    ##
    # Returns a string representation of the data passed in. It is assumed that
    # if this call runs, you are recieving section data you recognize
    ##
    def Parse(self,data:str) -> str:
        raise NotImplementedError