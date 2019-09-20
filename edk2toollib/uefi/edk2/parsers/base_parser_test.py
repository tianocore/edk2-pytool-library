# @file guid_parser_test.py
# Contains unit test routines for the guid parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
from edk2toollib.uefi.edk2.parsers.base_parser import BaseParser


class TestBaseParser(unittest.TestCase):

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

    def test_process_garbage_input(self):
        parser = BaseParser("")
        # make sure we fail the garbage input
        conditional_count = len(parser.ConditionalStack)
        self.assertFalse(parser.ProcessConditional("GARBAGE INPUT"))
        # make sure our coutn didn't change
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
        # check that a hex number doesn't exqual itself
        self.assertTrue(parser.ProcessConditional("!IF 0x30 == 30"))
        self.assertFalse(parser.InActiveCode())

    def test_process_conditional_greater_than(self):
        parser = BaseParser("")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 30 > 50"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 30 > 30"))
        self.assertFalse(parser.InActiveCode())

    def test_process_conditional_less_than(self):
        parser = BaseParser("")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 70 < 50"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 70 < 70"))
        self.assertFalse(parser.InActiveCode())

    def test_process_conditional_greater_than_equal(self):
        parser = BaseParser("")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 30 >= 50"))
        self.assertFalse(parser.InActiveCode())
        parser.ProcessConditional("!endif")
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!IF 30 >= 30"))
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

    def test_process_conditional_not_equals_true_false(self):
        parser = BaseParser("")
        # check != with true and false
        self.assertTrue(parser.ProcessConditional("!IF TRUE != FALSE"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))

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

    def test_process_conditional_variables(self):
        parser = BaseParser("")
        # check variables
        with self.assertRaises(RuntimeError):
            parser.ProcessConditional("!ifdef")
        self.assertTrue(parser.ProcessConditional("!ifdef $VARIABLE"))
        self.assertFalse(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!ifdef VARIABLE"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertTrue(parser.ProcessConditional("!ifndef VARIABLE"))
        self.assertFalse(parser.InActiveCode())

    def test_process_conditional_reset(self):
        parser = BaseParser("")
        # test reset
        self.assertTrue(parser.ProcessConditional("!IF FALSE"))
        parser.ResetParserState()
        self.assertTrue(parser.InActiveCode())
        self.assertEqual(len(parser.ConditionalStack), 0)

    def test_is_guid(self):
        guid1 = "= { 0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x46, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }}"
        parser = BaseParser("")
        self.assertTrue(parser.IsGuidString(guid1))
        guid2 = "= { 0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x46, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }"
        self.assertFalse(parser.IsGuidString(guid2))
        guid3 = "= { 0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }}"
        self.assertFalse(parser.IsGuidString(guid3))
        guid4 = "= { 0xD3B36F, 0xD551, 0x11D4, {0x9A, 0x46, 0x0, 0x90, 0x27, 0x3F, 0xC1,0xD }}"
        #TODO make sure we are checking length?
        #self.assertFalse(parser.IsGuidString(guid4))
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
            guid2_result = parser.ParseGuid(guid2)

        guid2 = "{ 0xD3B36FbadC, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}"
        with self.assertRaises(RuntimeError):
            guid2_result = parser.ParseGuid(guid2)
