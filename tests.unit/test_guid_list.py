# @file guid_list_test.py
# Contains unit test routines for the guid list class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import shutil
import tempfile
import unittest

from edk2toollib.uefi.edk2.guid_list import GuidList, GuidListEntry


class TestGuidListEntry(unittest.TestCase):

    def test_valid_input(self):
        GUID = "66341ae8-668f-4192-b44d-5f87b868f041"
        NAME = "testguid"
        FILEPATH = os.path.dirname(os.path.abspath(__file__))
        t = GuidListEntry(NAME, GUID, FILEPATH)
        self.assertEqual(t.name, NAME)
        self.assertEqual(t.guid, GUID)
        self.assertEqual(t.absfilepath, FILEPATH)
        self.assertTrue(GUID in str(t))
        self.assertTrue(FILEPATH in str(t))
        self.assertTrue(NAME in str(t))


class TestGuidList(unittest.TestCase):

    SAMPLE_DEC_FILE = \
        """## @file
TestDecFile
##

[Defines]
  DEC_SPECIFICATION              = 0x00010005
  PACKAGE_NAME                   = TestDecParserPkg
  PACKAGE_UNI_FILE               = TestDecParserPkg.uni
  PACKAGE_GUID                   = 57e8a49e-1b3f-41a0-a552-55ad831c15a8
  PACKAGE_VERSION                = 0.1

[Includes]
  Include

[LibraryClasses]
  ##  @libraryclass  Provide comment for fakelib
  #
  FakeLib|Include/Library/FakeLib.h

[Guids]
  gFakeTokenSpace =  {0x7c004f69, 0xd730, 0x4904, {0x83, 0xe1, 0x4b, 0xbf, 0x39, 0x3a, 0xfc, 0xb1}}
  gFake2TokenSpace = {0x7c004f69, 0xd730, 0x4904, {0x83, 0xe1, 0x4b, 0xbf, 0x39, 0x3a, 0xfc, 0xb2}}
  gFakeT3okenSpace = {0x7c004f69, 0xd730, 0x4904, {0x83, 0xe1, 0x4b, 0xbf, 0x39, 0x3a, 0xfc, 0xb3}}

[Protocols]
  ## None
  gFakeProtocol     = {0xe63e2ccd, 0x786e, 0x4754, {0x96, 0xf8, 0x5e, 0x88, 0xa3, 0xf0, 0xaf, 0x85}}

[Ppis]
  gFakePpi  =  {0xeeef868e, 0x5bf5, 0x4e48, {0x92, 0xa1, 0xd7, 0x6e, 0x02, 0xe5, 0xb9, 0xa7}}
  gFake2Ppi =  {0xeeef868e, 0x5bf5, 0x4e48, {0x92, 0xa1, 0xd7, 0x6e, 0x02, 0xe5, 0xb9, 0xa8}}

[UserExtensions.TianoCore."ExtraFiles"]
  PcAtChipsetPkgExtra.uni
"""

    SAMPLE_INF_FILE = \
        """## @file
#  Sample UEFI Application Reference EDKII Module.
#
#  This is a sample shell application that will print "UEFI Hello World!" to the
#  UEFI Console based on PCD setting.
#
#  It demos how to use EDKII PCD mechanism to make code more flexible.
#
#  Copyright (c) 2008 - 2018, Intel Corporation. All rights reserved.<BR>
#
#  SPDX-License-Identifier: BSD-2-Clause-Patent
#
#
##

[Defines]
  INF_VERSION                    = 0x00010005
  BASE_NAME                      = HelloWorld
  MODULE_UNI_FILE                = HelloWorld.uni
  FILE_GUID                      = 6987936E-ED34-44db-AE97-1FA5E4ED2116
  MODULE_TYPE                    = UEFI_APPLICATION
  VERSION_STRING                 = 1.0
  ENTRY_POINT                    = UefiMain

#
#  This flag specifies whether HII resource section is generated into PE image.
#
  UEFI_HII_RESOURCE_SECTION      = TRUE

#
# The following information is for reference only and not required by the build tools.
#
#  VALID_ARCHITECTURES           = IA32 X64 EBC
#

[Sources]
  HelloWorld.c
  HelloWorldStr.uni

[Packages]
  MdePkg/MdePkg.dec
  MdeModulePkg/MdeModulePkg.dec

[LibraryClasses]
  UefiApplicationEntryPoint
  UefiLib
  PcdLib

[FeaturePcd]
  gEfiMdeModulePkgTokenSpaceGuid.PcdHelloWorldPrintEnable   ## CONSUMES

[Pcd]
  gEfiMdeModulePkgTokenSpaceGuid.PcdHelloWorldPrintString   ## SOMETIMES_CONSUMES
  gEfiMdeModulePkgTokenSpaceGuid.PcdHelloWorldPrintTimes    ## SOMETIMES_CONSUMES

[UserExtensions.TianoCore."ExtraFiles"]
  HelloWorldExtra.uni
"""

    def __init__(self, *args, **kwargs):
        self.test_dir = None
        super().__init__(*args, **kwargs)

    def prep_workspace(self):
        self.clean_workspace()
        self.test_dir = os.path.realpath(tempfile.mkdtemp())

    def clean_workspace(self):
        if self.test_dir is None:
            return
        if os.path.isdir(self.test_dir):
            shutil.rmtree(self.test_dir)
            self.test_dir = None

    def setUp(self):
        self.prep_workspace()

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        self.clean_workspace()

    def test_valid_input(self):
        # write dec and inf sample files to tempdir
        with open(os.path.join(self.test_dir, "test.dec"), "w") as f:
            f.write(TestGuidList.SAMPLE_DEC_FILE)
        with open(os.path.join(self.test_dir, "test.inf"), "w") as f:
            f.write(TestGuidList.SAMPLE_INF_FILE)

        ResultList = GuidList.guidlist_from_filesystem(self.test_dir)
        self.assertEqual(len(ResultList), 8)

    def test_valid_input_recursive_filesystem(self):
        # write dec and inf sample files to tempdir
        os.makedirs(os.path.join(self.test_dir, "Build"))
        with open(os.path.join(self.test_dir, "Build", "test.dec"), "w") as f:
            f.write(TestGuidList.SAMPLE_DEC_FILE)
        with open(os.path.join(self.test_dir, "test.inf"), "w") as f:
            f.write(TestGuidList.SAMPLE_INF_FILE)

        ResultList = GuidList.guidlist_from_filesystem(self.test_dir)
        self.assertEqual(len(ResultList), 8)

    def test_incomplete_inf_contents(self):
        # write dec and inf sample files to tempdir
        with open(os.path.join(self.test_dir, "test.dec"), "w") as f:
            f.write(TestGuidList.SAMPLE_DEC_FILE)
        with open(os.path.join(self.test_dir, "test.inf"), "w") as f:
            f.write(TestGuidList.SAMPLE_INF_FILE.replace("BASE_NAME", "INVALID"))

        ResultList = GuidList.guidlist_from_filesystem(self.test_dir)
        self.assertEqual(len(ResultList), 7)

    def test_incomplete_dec_contents(self):
        # write dec and inf sample files to tempdir
        with open(os.path.join(self.test_dir, "test.dec"), "w") as f:
            f.write(TestGuidList.SAMPLE_DEC_FILE.replace("PACKAGE_NAME", "GARBAGE"))
        with open(os.path.join(self.test_dir, "test.inf"), "w") as f:
            f.write(TestGuidList.SAMPLE_INF_FILE)

        ResultList = GuidList.guidlist_from_filesystem(self.test_dir)
        self.assertEqual(len(ResultList), 7)

    def test_unsupported_file_type(self):
        # write dec and inf sample files to tempdir
        with open(os.path.join(self.test_dir, "test.unsupported_dec"), "w") as f:
            f.write(TestGuidList.SAMPLE_DEC_FILE)
        with open(os.path.join(self.test_dir, "test.unsupported_inf"), "w") as f:
            f.write(TestGuidList.SAMPLE_INF_FILE)

        ResultList = GuidList.guidlist_from_filesystem(self.test_dir)
        self.assertEqual(len(ResultList), 0)

    def test_ignore_file_pattern(self):
        # write dec and inf sample files to tempdir
        with open(os.path.join(self.test_dir, "test.dec"), "w") as f:
            f.write(TestGuidList.SAMPLE_DEC_FILE)
        with open(os.path.join(self.test_dir, "test.inf"), "w") as f:
            f.write(TestGuidList.SAMPLE_INF_FILE)

        ResultList = GuidList.guidlist_from_filesystem(self.test_dir, ["*.inf"])
        self.assertEqual(len(ResultList), 7)

    def test_ignore_folder_pattern(self):
        # write dec and inf sample files to tempdir
        os.makedirs(os.path.join(self.test_dir, "my_ignore"))
        with open(os.path.join(self.test_dir, "my_ignore", "test.dec"), "w") as f:
            f.write(TestGuidList.SAMPLE_DEC_FILE)
        with open(os.path.join(self.test_dir, "test.inf"), "w") as f:
            f.write(TestGuidList.SAMPLE_INF_FILE)

        ResultList = GuidList.guidlist_from_filesystem(self.test_dir, ["my_ignore"])
        self.assertEqual(len(ResultList), 1)

    def test_ignore_file_pattern2(self):
        # write dec and inf sample files to tempdir
        os.makedirs(os.path.join(self.test_dir, "my_ignore"))
        with open(os.path.join(self.test_dir, "my_ignore", "test.dec"), "w") as f:
            f.write(TestGuidList.SAMPLE_DEC_FILE)
        with open(os.path.join(self.test_dir, "test.inf"), "w") as f:
            f.write(TestGuidList.SAMPLE_INF_FILE)

        ResultList = GuidList.guidlist_from_filesystem(self.test_dir, ["my_ignore/test.dec"])
        self.assertEqual(len(ResultList), 1)
