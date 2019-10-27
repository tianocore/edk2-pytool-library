# @file base_parser_test.py
# Partial unit test for base parser
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
from edk2toollib.uefi.edk2.parsers.base_parser import BaseParser


class TestBaseParser(unittest.TestCase):

    def test_replace_macro_using_dollarsign(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "sean"
        })
        line = "Hello $(name)!"
        self.assertEqual(parser.ReplaceVariables(line), "Hello sean!")

    def test_replace_macro_local_var_priority(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "sean"
        })
        parser.LocalVars["name"] = "fred"
        line = "Hello $(name)!"
        self.assertEqual(parser.ReplaceVariables(line), "Hello fred!")

    def test_replace_macro_without_resolution(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "sean"
        })
        line = "Hello $(Unknown_Token)!"
        self.assertEqual(parser.ReplaceVariables(line), "Hello 0!")

    def test_replace_macro_ifdef_dollarsign(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "sean"
        })
        line = "!ifdef $(name)"
        self.assertEqual(parser.ReplaceVariables(line), "!ifdef sean")

        line = "!ifdef $(Invalid_Token)"
        self.assertEqual(parser.ReplaceVariables(line), "!ifdef 0")

        line = "!IFDEF $(name)"
        self.assertEqual(parser.ReplaceVariables(line), "!IFDEF sean")

    def test_replace_macro_ifndef_dollarsign(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "sean"
        })
        line = "!IfNDef $(name)"
        self.assertEqual(parser.ReplaceVariables(line), "!IfNDef sean")

        line = "!ifndef $(Invalid_Token)"
        self.assertEqual(parser.ReplaceVariables(line), "!ifndef 0")

        line = "!IFnDEF $(name)"
        self.assertEqual(parser.ReplaceVariables(line), "!IFnDEF sean")

    def test_replace_macro_ifdef(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "sean"
        })
        line = "!ifdef name"
        self.assertEqual(parser.ReplaceVariables(line), "!ifdef sean")

        line = "!ifdef Invalid_Token"
        self.assertEqual(parser.ReplaceVariables(line), "!ifdef 0")

        line = "!IFDEF name"
        self.assertEqual(parser.ReplaceVariables(line), "!IFDEF sean")

    def test_replace_macro_ifndef(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "sean"
        })
        line = "!IfNDef name"
        self.assertEqual(parser.ReplaceVariables(line), "!IfNDef sean")

        line = "!ifndef Invalid_Token"
        self.assertEqual(parser.ReplaceVariables(line), "!ifndef 0")

        line = "!IFnDEF name"
        self.assertEqual(parser.ReplaceVariables(line), "!IFnDEF sean")
