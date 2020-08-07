# @file cper_section_data_parser.py
# Base class for all parsing types
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

class SECTION_PARSER_PLUGIN(object):

    def __init__(self):
        pass

    def CanParse(self,guid):
        raise NotImplementedError

    def Parse(self,data):
        raise NotImplementedError