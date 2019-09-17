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
        # make sure we fail the garbage input
        conditional_count = len(parser.ConditionalStack)
        self.assertFalse(parser.ProcessConditional("GARBAGE INPUT"))
        # make sure our coutn didn't change
        self.assertEqual(len(parser.ConditionalStack), conditional_count)
        # pop off the false statement and make sure we're back to active code
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertTrue(parser.InActiveCode())
        # check that nothing is on the stack
        self.assertEqual(len(parser.ConditionalStack), 0)

    def test_process_conditional_ands_ors(self):
        parser = BaseParser("")

        # make sure we can't do 5 tokens
        with self.assertRaises(RuntimeError):
            parser.ProcessConditional("!if 3 == 6 ==")

        # TODO: check for and and if once we've implemented this

    def test_process_conditional_longer_tokens(self):
        parser = BaseParser("")

        # make sure we can't do three tokens
        with self.assertRaises(RuntimeError):
            parser.ProcessConditional("!if 3 ==")

        # check 4 tokens
        self.assertTrue(parser.ProcessConditional("!IF 30 > 50"))
        self.assertFalse(parser.InActiveCode())
        # check else
        self.assertTrue(parser.ProcessConditional("!else"))
        self.assertTrue(parser.InActiveCode())
        self.assertTrue(parser.ProcessConditional("!EnDiF"))
        self.assertTrue(parser.InActiveCode())
        # check that nothing is on the stack
        self.assertEqual(len(parser.ConditionalStack), 0)
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
