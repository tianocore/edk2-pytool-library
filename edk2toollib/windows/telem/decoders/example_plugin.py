# @file a_test_plugin.py
# A testing plugin used to verify parsing
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import uuid
from edk2toollib.windows.telem.cper_section_data import SECTION_DATA_PARSER


class EXAMPLE_PLUGIN(SECTION_DATA_PARSER):

    def __init__(self, data=b''):
        super.__init__(data)

    ##
    # Returns string representation of this parser
    ##
    def __str__(self) -> str:
        return "EXAMPLE PLUGIN"

    ##
    # True if this parser recognizes the input guid
    ##
    def CanParse(self, guid: uuid) -> bool:
        return False

    ##
    # Returns a string representation of the data passed in. It is assumed that
    # if this call runs, you are recieving section data you recognize
    ##
    def Parse(self, pretty: bool, data: str) -> str:
        return ""
