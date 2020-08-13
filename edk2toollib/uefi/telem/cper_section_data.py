# @file cper_section_data.py
# Base class for all parsing types
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

class SECTION_PARSER_PLUGIN(object):

    def __str__(self) -> str:
        raise NotImplementedError

    def CanParse(self,guid) -> bool:
        raise NotImplementedError

    def Parse(self,data) -> str:
        raise NotImplementedError