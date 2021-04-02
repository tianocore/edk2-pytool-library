# @file cper_section_data.py
# Base class for all parsing types
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import uuid


class SECTION_DATA_PARSER(object):

    ##
    # Instantiate this parser. Simply use a blank bytes object for data
    # if the instantiator did not pass in data (use case: checking if this
    # plugin can parse prior to storing an object version)
    ##
    def __init__(self, data=b''):
        self.raw_input = data

    ##
    # Returns string representation of this parser
    ##
    def __str__(self) -> str:
        return "UNNAMED PARSER"

    ##
    # True if this parser recognizes the input guid
    ##
    def CanParse(self, guid: uuid) -> bool:
        raise NotImplementedError

    ##
    # Returns a string representation of the data passed in. It is assumed that
    # if this call runs, you are recieving section data you recognize
    ##
    def Parse(self, friendly: bool, data: str) -> str:
        raise NotImplementedError
