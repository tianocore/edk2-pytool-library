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

    def test_process_conditional(self):
      parser = BaseParser()
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
