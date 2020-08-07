# @file cper_section_data_parser.py
# Code to help parse cper header
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

# TODO: This will be the archetype for plugins

class SECTION_PARSER_PLUGIN(object):

    def __init__(self):
        pass

    def CanParse(self,guid):
        raise NotImplementedError

    def Parse(self,data):
        raise NotImplementedError