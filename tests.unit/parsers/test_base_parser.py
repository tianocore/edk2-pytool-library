# @file base_parser_test.py
# Contains unit test routines for the base parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import tempfile
import unittest

from edk2toollib.uefi.edk2.parsers.base_parser import BaseParser
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class TestBaseParser(unittest.TestCase):

    def test_replace_boolean_constants(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "true": "True",
            "false": "False",
            "b_true": True,
            "b_false": False
        })
        line = "$(true)"
        self.assertEqual(parser.ReplaceVariables(line), "TRUE")
        line = "$(false)"
        self.assertEqual(parser.ReplaceVariables(line), "FALSE")
        line = "$(b_true)"
        self.assertEqual(parser.ReplaceVariables(line), "TRUE")
        line = "$(b_false)"
        self.assertEqual(parser.ReplaceVariables(line), "FALSE")

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


class TestBaseParserConditionals(unittest.TestCase):

    def test_replace_macro_without_resolution(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "sean"
        })
        line = "!if $(Unknown_Token)!"
        self.assertEqual(parser.ReplaceVariables(line), "!if 0!")

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

    def test_replace_macro_elseif(self):
        parser = BaseParser("")
        parser.SetInputVars({
            "name": "matt"
        })
        line = "!elseif $(name)"
        self.assertEqual(parser.ReplaceVariables(line), "!elseif matt")

        line = "!ELSEIF $(Invalid_Token)"
        self.assertEqual(parser.ReplaceVariables(line), "!ELSEIF 0")

    def test_conditional_ifdef(self):
        parser = BaseParser("")

        # simple confirmation of expected behavior
        # don't need to test VariableReplacement
        # that is done in the tests replace methods
        self.assertTrue(parser.InActiveCode())
        parser.ProcessConditional("!ifdef 0")
        self.assertFalse(parser.InActiveCode())
        parser.PopConditional()

        self.assertTrue(parser.InActiveCode())
        parser.ProcessConditional("!ifdef blahblah")
        self.assertTrue(parser.InActiveCode())
        parser.PopConditional()

    def test_conditional_ifndef(self):
        parser = BaseParser("")

        # simple confirmation of expected behavior
        # don't need to test VariableReplacement
        # that is done in the tests replace methods
        self.assertTrue(parser.InActiveCode())
        parser.ProcessConditional("!ifndef 0")
        self.assertTrue(parser.InActiveCode())
        parser.PopConditional()

        self.assertTrue(parser.InActiveCode())
        parser.ProcessConditional("!ifndef blahblah")
        self.assertFalse(parser.InActiveCode())
        parser.PopConditional()

    def test_process_conditional_single_boolean(self):
        parser = BaseParser("")
        # check that nothing is on the stack
        self.assertEqual(len(parser.ConditionalStack), 0)
        # check that we're in active code
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF TRUE"))
        # make sure we've added some to the stack - should we even be checking this?
        self.assertEqual(len(parser.ConditionalStack), 1)
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF FALSE"))
        self.assertFalse(parser.InActiveCode())
        # make sure if pass in a true thing we aren't back in active
        self.assertTrue(parser.ProcessConditional("!IF TRUE"))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertFalse(parser.InActiveCode())
        # pop off the false statement and make sure we're back to active code
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertTrue(parser.InActiveCode())
        # check that nothing is on the stack
        self.assertEqual(len(parser.ConditionalStack), 0)
        # lower case false
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF false"))
        self.assertFalse(parser.InActiveCode())

    def test_process_garbage_input(self):
        parser = BaseParser("")
        # make sure we fail the garbage input
        conditional_count = len(parser.ConditionalStack)
        self.assertFalse(parser.ProcessConditional("GARBAGE INPUT"))
        # make sure our count didn't change
        self.assertEqual(len(parser.ConditionalStack), conditional_count)

    def test_process_conditional_ands_ors(self):
        parser = BaseParser("")
        self.assertTrue(parser.ProcessConditional("!if TRUE == FALSE OR TRUE == TRUE"))
        # enable this once we have working and and or but for now just test it
        # self.assertTrue(parser.InActiveCode())
        # TODO: check for and and if once we've implemented this
        # check for nested things etc

    def test_process_extra_tokens(self):
        parser = BaseParser("")
        # make sure we can't do 5 tokens
        with self.assertRaises(RuntimeError):
            parser.ProcessConditional("!if 3 == 6 ==")

        # make sure we can't do three tokens
        with self.assertRaises(RuntimeError):
            parser.ProcessConditional("!if 3 ==")

    def test_process_conditional_hex_number(self):
        parser = BaseParser("")
        # check that a hex number doesn't equal itself
        self.assertTrue(parser.ProcessConditional("!IF 0x30 == 30"))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!endif"))
        # Check that two hex doesn't equal each other
        self.assertTrue(parser.ProcessConditional("!IF 0x20 == 0x30"))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!endif"))
        # check that hex equals decimal
        self.assertTrue(parser.ProcessConditional("!IF 0x20 == 32"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!endif"))
        # check that hex comparisons work
        self.assertTrue(parser.ProcessConditional("!IF 0x20 > 0x20"))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!endif"))
        self.assertTrue(parser.ProcessConditional("!IF 0x20 >= 0x20"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!endif"))

    def test_process_conditional_greater_than(self):
        parser = BaseParser("")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 30 > 50"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 30 > 30"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")
        self.assertTrue(parser.ProcessConditional("!IF 50 > 30"))
        self.assertTrue(parser.InActiveCode())

    def test_process_conditional_less_than(self):
        parser = BaseParser("")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 70 < 50"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")

        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 70 < 70"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")

        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 50 < 70"))
        self.assertTrue(parser.InActiveCode())

    def test_process_conditional_greater_than_equal(self):
        parser = BaseParser("")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 30 >= 50"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")

        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 30 >= 30"))
        self.assertTrue(parser.InActiveCode())
        parser.ProcessConditional("!endif")

        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 50 >= 30"))
        self.assertTrue(parser.InActiveCode())

    def test_process_conditional_less_than_equal(self):
        parser = BaseParser("")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 70 <= 50"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")

        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 70 <= 70"))
        self.assertTrue(parser.InActiveCode())
        parser.ProcessConditional("!endif")

        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 50 <= 70"))
        self.assertTrue(parser.InActiveCode())
        parser.ProcessConditional("!endif")

    def test_process_conditional_true_not_equals_false(self):
        parser = BaseParser("")
        # check != with true and false
        self.assertTrue(parser.ProcessConditional("!IF TRUE != FALSE"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))

    def test_process_conditional_not_equals_true_false(self):
        parser = BaseParser("")
        # check != with true and false
        self.assertTrue(parser.ProcessConditional("!IF RACECAR != RACECAR"))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertTrue(parser.ProcessConditional("!IF false != FALSE"))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))

    def test_process_conditional_false_equals_zero(self):
        parser = BaseParser("")
        self.assertTrue(parser.ProcessConditional("!IF FALSE == 0"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))

    def test_process_conditional_true_equals_one(self):
        parser = BaseParser("")
        # check != with true and false
        self.assertTrue(parser.ProcessConditional("!IF TRUE == 1"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))

    def test_process_conditional_true_cannot_be_greater_than(self):
        parser = BaseParser("")
        # check != with true and false
        with self.assertRaises(ValueError):
            parser.ProcessConditional("!IF TRUE >= 1")

    def test_process_conditional_true_cannot_be_greater_than_hex(self):
        parser = BaseParser("")
        # check != with true and false
        with self.assertRaises(ValueError):
            parser.ProcessConditional("!IF 0x7 >= TRUE")

    def test_process_conditional_non_numerical(self):
        parser = BaseParser("")
        # check non numerical values
        with self.assertRaises(ValueError):
            parser.ProcessConditional("!IF ROCKETSHIP > 50")
        with self.assertRaises(ValueError):
            parser.ProcessConditional("!if 50 < ROCKETSHIPS")

    def test_process_conditional_invalid_operators(self):
        parser = BaseParser("")
        # check weird operators
        with self.assertRaises(RuntimeError):
            self.assertTrue(parser.ProcessConditional("!IF 50 <> 50"))

    def test_process_bad_else(self):
        parser = BaseParser("")
        # check to make sure we can't do a malformed endif
        with self.assertRaises(RuntimeError):
            self.assertTrue(parser.ProcessConditional("!else test"))
        # try to pop the empty stack and invert it
        with self.assertRaises(IndexError):
            self.assertTrue(parser.ProcessConditional("!else"))

    def test_process_else(self):
        parser = BaseParser("")
        # check to make sure we can't do a malformed endif
        self.assertTrue(parser.ProcessConditional("!if TRUE"))
        self.assertTrue(parser.ProcessConditional("!else"))
        self.assertFalse(parser.InActiveCode())

    def test_process_bad_endif(self):
        parser = BaseParser("")
        # check to make sure we can't do a malformed endif
        with self.assertRaises(RuntimeError):
            self.assertTrue(parser.ProcessConditional("!endif test"))
        # try to pop the empty stack
        with self.assertRaises(IndexError):
            self.assertTrue(parser.ProcessConditional("!endif"))

    def test_process_conditional_variables(self):
        parser = BaseParser("")
        # check variables
        with self.assertRaises(RuntimeError):
            parser.ProcessConditional("!ifdef")
        with self.assertRaises(RuntimeError):
            parser.ProcessConditional("!ifndef")

    def test_process_conditional_reset(self):
        parser = BaseParser("")
        # test reset
        self.assertTrue(parser.ProcessConditional("!IF FALSE"))
        parser.ResetParserState()
        self.assertTrue(parser.InActiveCode())
        self.assertEqual(len(parser.ConditionalStack), 0)

    def test_process_in_conditional(self):
        parser = BaseParser("")
        parser.SetInputVars({"TOOL_CHAIN_TAG": "GCC5_TEST"})
        self.assertTrue(parser.ProcessConditional(
            '!if ("GCC49" in $(TOOL_CHAIN_TAG)) OR ("GCC5" in $(TOOL_CHAIN_TAG))'))
        self.assertTrue(parser.InActiveCode())
        parser.ResetParserState()
        parser.SetInputVars({"TOOL_CHAIN_TAG": "TESTGCC49"})
        self.assertTrue(parser.ProcessConditional(
            '!if ("GCC49" in $(TOOL_CHAIN_TAG)) OR ("GCC5" in $(TOOL_CHAIN_TAG))'))
        self.assertTrue(parser.InActiveCode())
        parser.ResetParserState()
        # Don't give it a tool chain tag that isn't in the things we're searching for
        parser.SetInputVars({"TOOL_CHAIN_TAG": "NOTFOUND"})
        self.assertTrue(parser.ProcessConditional(
            '!if ("GCC49" in $(TOOL_CHAIN_TAG)) OR ("GCC5" in $(TOOL_CHAIN_TAG))'))
        self.assertFalse(parser.InActiveCode())

    def test_process_or_operation_conditional(self):
        parser = BaseParser("")
        self.assertTrue(parser.EvaluateConditional('!IF TRUE OR FALSE'))
        self.assertTrue(parser.EvaluateConditional('!if FALSE OR TRUE'))
        self.assertTrue(parser.EvaluateConditional('!if FALSE || TRUE'))
        self.assertTrue(parser.EvaluateConditional('!if TRUE OR TRUE'))
        self.assertFalse(parser.EvaluateConditional('!if FALSE OR FALSE'))
        self.assertFalse(parser.EvaluateConditional('!if FALSE || FALSE'))

    def test_process_and_operation_conditional(self):
        parser = BaseParser("")
        self.assertFalse(parser.EvaluateConditional('!if TRUE AND FALSE'))
        self.assertFalse(parser.EvaluateConditional('!if FALSE AND TRUE'))
        self.assertTrue(parser.EvaluateConditional('!if TRUE AND TRUE'))
        self.assertTrue(parser.EvaluateConditional('!if TRUE && TRUE'))
        self.assertFalse(parser.EvaluateConditional('!if FALSE AND FALSE'))
        self.assertFalse(parser.EvaluateConditional('!if FALSE && FALSE'))

    def test_process_invalid_conditional(self):
        parser = BaseParser("")
        with self.assertRaises(RuntimeError):
            parser.EvaluateConditional('!if TRUE AND FALSE AND')
        with self.assertRaises(RuntimeError):
            parser.EvaluateConditional('TRUE AND FALSE AND')

    def test_emulator_conditional_or_double_in(self):
        parser = BaseParser("")
        parser.SetInputVars({"ARCH": "X64"})
        self.assertTrue(parser.ProcessConditional(
            '!if "IA32" in $(ARCH) || "X64" in $(ARCH)'))
        self.assertTrue(parser.InActiveCode())
        parser.ResetParserState()
        parser.SetInputVars({"ARCH": "IA32"})
        self.assertTrue(parser.ProcessConditional(
            '!if "IA32" in $(ARCH) || "X64" in $(ARCH)'))
        self.assertTrue(parser.InActiveCode())
        parser.ResetParserState()

    def test_emulator_conditional_not_in(self):
        parser = BaseParser("")
        parser.SetInputVars({"TOOL_CHAIN_TAG": "VS2019"})
        self.assertTrue(parser.ProcessConditional('!if "XCODE5" not in $(TOOL_CHAIN_TAG)'))
        self.assertTrue(parser.InActiveCode())
        parser.ResetParserState()

    def test_emulator_conditional_parens_order(self):
        '''Makes sure the parenthesis affect the order of expressions'''
        parser = BaseParser("")
        self.assertFalse(parser.EvaluateConditional('!if TRUE OR FALSE AND FALSE'))
        self.assertTrue(parser.EvaluateConditional('!if TRUE OR (FALSE AND FALSE)'))
        parser.ResetParserState()

    def test_emulator_conditional_not_or(self):
        '''Makes sure we can use the not with other operators'''
        parser = BaseParser("")
        self.assertTrue(parser.EvaluateConditional('!if FALSE NOT OR FALSE'))
        self.assertFalse(parser.EvaluateConditional('!if TRUE NOT OR FALSE'))
        self.assertFalse(parser.EvaluateConditional('!if FALSE NOT OR TRUE'))
        self.assertFalse(parser.EvaluateConditional('!if TRUE NOT OR TRUE'))

    def test_emulator_conditional_not_it_all(self):
        '''Makes sure the parenthesis affect the order of expressions'''
        parser = BaseParser("")
        self.assertTrue(parser.EvaluateConditional('!if NOT FALSE OR FALSE'))
        self.assertFalse(parser.EvaluateConditional('!if NOT TRUE OR FALSE'))
        # check to make sure it works with parenthesis
        self.assertFalse(parser.EvaluateConditional('!if NOT(TRUE)'))
        self.assertTrue(parser.EvaluateConditional('!if NOT(FALSE)'))
        # make sure it works with the bang symbol
        self.assertFalse(parser.EvaluateConditional('!if !(TRUE)'))
        self.assertTrue(parser.EvaluateConditional('!if !(FALSE)'))

        parser.ResetParserState()

    def test_conditional_with_variable(self):
        '''Makes sure conversions are correct when using variables'''
        parser = BaseParser("")
        parser.LocalVars = {"MAX_SOCKET": '4', 'TARGET': 'DEBUG'}

        self.assertTrue(parser.ProcessConditional('!if $(MAX_SOCKET) <= 4'))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

        self.assertTrue(parser.ProcessConditional('!if $(TARGET) == "DEBUG" && $(MAX_SOCKET) <= 4'))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

        self.assertTrue(parser.ProcessConditional('!if $(MAX_SOCKET) <= 3'))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

        self.assertTrue(parser.ProcessConditional('!if ($(TARGET) == "RELEASE") && ($(MAX_SOCKET) <= 4)'))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

    def test_conditional_without_spaces(self):
        parser = BaseParser("")
        parser.LocalVars = {"MAX_SOCKET": '4'}

        self.assertTrue(parser.ProcessConditional('!if $(MAX_SOCKET)<=4'))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

        self.assertTrue(parser.ProcessConditional('!if $(MAX_SOCKET) <=4'))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

        self.assertTrue(parser.ProcessConditional('!if $(MAX_SOCKET)<= 4'))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

        self.assertTrue(parser.ProcessConditional('!if $(MAX_SOCKET)>=4'))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

        self.assertTrue(parser.ProcessConditional('!if $(MAX_SOCKET)==4'))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))

        self.assertTrue(parser.ProcessConditional('!if $(MAX_SOCKET)!=4'))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional('!endif'))


class TestBaseParserGuids(unittest.TestCase):

    def test_is_guid(self):
        guid1 = "= { 0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x46, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }}"
        parser = BaseParser("")
        self.assertTrue(parser.IsGuidString(guid1))
        guid2 = "= { 0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x46, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }"
        self.assertFalse(parser.IsGuidString(guid2))
        guid3 = "= { 0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }}"
        self.assertFalse(parser.IsGuidString(guid3))
        # guid4 = "= { 0xD3B36F, 0xD551, 0x11D4, {0x9A, 0x46, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }}"
        # TODO make sure we are checking length?
        # self.assertFalse(parser.IsGuidString(guid4))
        guid5 = " { 0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x46, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }}"
        self.assertFalse(parser.IsGuidString(guid5))

    def test_parse_guid(self):
        guid1 = "{ 0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x46, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }}"
        guid1_answer = "D3B36F2C-D551-11D4-9A46-0090273FC10D"
        parser = BaseParser("")
        guid1_result = parser.ParseGuid(guid1)
        self.assertEqual(guid1_answer, guid1_result)
        # try a bad guid and make sure it fails since it's missing an element
        guid2 = "{ 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1 }}"
        with self.assertRaises(RuntimeError):
            parser.ParseGuid(guid2)

        # check one that's too long
        guid3 = "{ 0xD3B36FbadC, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}"
        with self.assertRaises(RuntimeError):
            parser.ParseGuid(guid3)

        # check one that's too short
        guid4 = "{ 0x3, 0x1, 0x4, { 0xA, 0x6, 0x0, 0x9, 0x2, 0xF, 0x1, 0xD }}"
        guid4_answer = "00000003-0001-0004-0A06-0009020F010D"
        guid4_result = parser.ParseGuid(guid4)
        self.assertEqual(guid4_result, guid4_answer)


class TestBaseParserVariables(unittest.TestCase):

    def test_replace_input_variables(self):
        parser = BaseParser("")
        variables = {
            "FIFTY": 50,
            "TEST": "TEST",
            "LOWER NUMBER": 40,
            "HEX": "0x20",
            "BOOLEAN TRUE": "TRUE",
            "BOOLEAN FALSE": "FALSE",
        }
        parser.SetInputVars(variables)
        # check to make sure we don't modify if we don't have variables
        no_var = "this has no variables"
        no_var_result = parser.ReplaceVariables(no_var)
        self.assertEqual(no_var_result, no_var)
        # make sure we don't fail when we have unknown variables
        na_var = "unknown var $(UNKNOWN)"
        na_var_after = "unknown var $(UNKNOWN)"
        na_var_result = parser.ReplaceVariables(na_var)
        self.assertEqual(na_var_result, na_var_after)
        # make sure we're good for all the variables
        variable_str = "var $(%s)"
        for variable_key in variables:
            line = variable_str % variable_key
            result = parser.ReplaceVariables(line)
            val = "var " + str(variables[variable_key])
            self.assertEqual(result, val)

    def test_replace_local_variables(self):
        parser = BaseParser("")
        variables = {
            "FIFTY": 50,
            "TEST": "TEST",
            "LOWER NUMBER": 40,
            "HEX": "0x20",
            "BOOLEAN": "TRUE",
            "BOOLEAN FALSE": "FALSE",
        }
        parser.LocalVars = variables
        # check to make sure we don't modify if we don't have variables
        no_var = "this has no variables"
        no_var_result = parser.ReplaceVariables(no_var)
        self.assertEqual(no_var_result, no_var)
        # make sure we don't fail when we have unknown variables
        na_var = "unknown var $(UNKNOWN)"
        na_var_after = "unknown var $(UNKNOWN)"
        na_var_result = parser.ReplaceVariables(na_var)
        self.assertEqual(na_var_result, na_var_after)
        # make sure we're good for all the variables
        variable_str = "var $(%s)"
        for variable_key in variables:
            line = variable_str % variable_key
            result = parser.ReplaceVariables(line)
            val = "var " + str(variables[variable_key])
            self.assertEqual(result, val)


class TestBaseParserPathAndFile(unittest.TestCase):

    # because of how this works we use WriteLines, SetAbsPath, and SetPackagePath
    def test_find_path(self):
        # we're using write lines to make sure everything wo
        parser = BaseParser("")
        parser.Lines = ["hello"]
        package_paths = ["Common/Test", "SM_MAGIC"]
        root_path = tempfile.mkdtemp()
        index = 0
        # create the packages path folders
        for package in package_paths:
            pack_path = os.path.join(root_path, package)
            os.makedirs(pack_path)
            parser.WriteLinesToFile(os.path.join(pack_path, f"package_{index}.txt"))
            index += 1
        # setup the parser
        pathobj = Edk2Path(root_path, package_paths)
        parser.SetEdk2Path(pathobj)

        # create the root and target files
        root_file = "root.txt"
        target_file = "target.txt"

        root_filepath = os.path.join(root_path, root_file)
        target_filedir = os.path.join(root_path, "BuildPkg")
        target_filepath = os.path.join(target_filedir, target_file)
        # create root file
        parser.WriteLinesToFile(root_filepath)
        # create target file
        os.makedirs(target_filedir)
        parser.WriteLinesToFile(target_filepath)
        parser.TargetFilePath = target_filepath
        # check if we can find the root
        root_found = parser.FindPath(root_file)
        self.assertEqual(root_found, root_filepath)
        # check we can find the target using the target path
        target_found = parser.FindPath(target_file)
        self.assertEqual(target_found, target_filepath)

        # check package relative packages
        for index in range(len(package_paths)):
            file_name = f"package_{index}.txt"
            pp_found = parser.FindPath(file_name)
            self.assertTrue(os.path.exists(pp_found))

        # invalid files
        invalid_filename = "YOU_WONT_FIND_ME.txt"
        invalid_file = os.path.join(root_path, invalid_filename)
        invalid_result = parser.FindPath(invalid_file)
        invalid_result2 = parser.FindPath(invalid_filename)
        self.assertEqual(None, invalid_result)
        self.assertEqual(None, invalid_result2)
        invalid_result3 = parser.FindPath(None)
        self.assertEqual(None, invalid_result3)

    # make sure we can write out to a file

    def test_write_lines(self):
        parser = BaseParser("")
        parser.Lines = ["hello"]
        root_path = tempfile.mkdtemp()
        file_path = os.path.join(root_path, "lines.txt")
        parser.WriteLinesToFile(file_path)
        self.assertTrue(os.path.exists(file_path))
        # TODO check to make sure that the file matches what we expect
