# @file recipe_parser_test.py
# Contains unit test routines for the dsc => recipe functionality.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import os
import tempfile
from edk2toollib.uefi.edk2.build_objects.recipe import recipe
from edk2toollib.uefi.edk2.build_objects.recipe import pcd
from edk2toollib.uefi.edk2.build_objects.recipe import sku_id
from edk2toollib.uefi.edk2.build_objects.recipe import library
from edk2toollib.uefi.edk2.build_objects.recipe import component
from edk2toollib.uefi.edk2.build_objects.recipe import source_info


class TestRecipe(unittest.TestCase):

    def test_null_creation(self):
        rec = recipe()
        self.assertIsNotNone(rec)

    def test_add_sku(self):
        rec = recipe()
        sku1 = sku_id()
        sku1_bad = sku_id(name="TEST2")
        sku2 = sku_id(1, "TEST")
        sku2_bad = sku_id(2, "TEST")

        rec.skus.add(sku1)
        rec.skus.add(sku1_bad)
        print(rec.skus)
        self.assertEqual(len(rec.skus), 1)
        rec.skus.add(sku2)
        rec.skus.add(sku2_bad)
        print(rec.skus)
        self.assertEqual(len(rec.skus), 2)

    def test_add_component(self):
        rec = recipe()
        comp1 = component("test1.inf", [])
        comp2 = component("test2.inf")
        comp1_bad = component("test1.inf", [], source_info("test.dsc", 50))
        comp3 = component("test3.inf", ["PHASE"])
        comp3_good = component("test3.inf", ["PHASE2"])

        rec.components.add(comp1)
        rec.components.add(comp2)
        self.assertEqual(len(rec.components), 2, rec.components)
        rec.components.add(comp1_bad)
        self.assertEqual(len(rec.components), 2)
        rec.components.add(comp3)
        self.assertEqual(len(rec.components), 3)
        rec.components.add(comp3_good)
        self.assertEqual(len(rec.components), 4)


class TestComponent(unittest.TestCase):

    def test_null_creation(self):
        comp = component("test.inf")
        self.assertIsNotNone(comp)

    def test_add_pcd(self):
        comp = component("test.inf")
        pcd1 = pcd("namespace", "name", "TRUE")
        pcd2 = pcd("namespace", "name2")
        pcd1_bad = pcd("namespace", "name", "FALSE")
        comp.pcds.add(pcd1)
        comp.pcds.add(pcd2)
        self.assertEqual(len(comp.pcds), 2)
        comp.pcds.add(pcd1_bad)
        self.assertEqual(len(comp.pcds), 2)

    def test_add_library(self):
        comp = component("test.inf")
        lib1 = library("BaseLib", "test1.inf")
        lib2 = library("BaseLib2", "test2.inf")
        lib1_bad = library("BaseLib", "test3.inf")

        comp.libraries.add(lib1)
        comp.libraries.add(lib2)
        self.assertEqual(len(comp.libraries), 2)
        comp.libraries.add(lib1_bad)
        self.assertEqual(len(comp.libraries), 2)

        null_lib1 = library("NULL", "test1.inf")
        null_lib2 = library("NULL", "test2.inf")
        null_lib1_bad = library("NULL", "test2.inf")

        comp.libraries.add(null_lib1)
        comp.libraries.add(null_lib2)
        self.assertEqual(len(comp.libraries), 4)
        comp.libraries.add(null_lib1_bad)
        self.assertEqual(len(comp.libraries), 4)


class TestLibrary(unittest.TestCase):

    def test_null_creation(self):
        comp = library("test", "test.inf")
        self.assertIsNotNone(comp)


class TestPcd(unittest.TestCase):

    def test_null_creation(self):
        pcd1 = pcd("Namespace", "Name")
        self.assertIsNotNone(pcd1)
        pcd2 = pcd("Namespace", "Name", "VALUE")
        self.assertIsNotNone(pcd2)


class TestSourceInfo(unittest.TestCase):

    def test_null_creation(self):
        source = source_info("inf", 50)
        self.assertIsNotNone(source)
