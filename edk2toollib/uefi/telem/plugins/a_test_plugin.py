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

class A_TEST_PLUGIN(SECTION_PARSER_PLUGIN):

    def __init__(self):
        pass

    def __str__(self):
        return "TEST PARSER"

    def CanParse(self,guid):
        return False

    def Parse(self,data):
        pass