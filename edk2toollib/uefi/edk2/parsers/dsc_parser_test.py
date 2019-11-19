# @file dsc_parser_test.py
# Partial unit test for dsc parser
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
from edk2toollib.uefi.edk2.parsers.dsc_parser import DscParser
import tempfile
import os
import urllib.request

class TestDscParser(unittest.TestCase):

    def download_file(self, url, file_path):
      urllib.request.urlretrieve(url, file_path)

    def test_process_kablylake_rvp3_pcd_dsc(self):
        # first we download the DSC we care about
        dsc_location = tempfile.mkdtemp()
        commit = "3badb2a8e8b56191d8a3f8417c984c497568aee6"
        dsc_file = "Intel/KabylakeOpenBoardPkg/KabylakeRvp3/OpenBoardPkgPcd.dsc"
        url = f"https://raw.githubusercontent.com/tianocore/edk2-platforms/{commit}/Platform/{dsc_file}"
        file_path = os.path.join(dsc_location, "test.dsc")
        self.download_file(url, file_path)
        # next we need to process the DSC
        parser = DscParser()
        print(f"Downloaded file to {file_path}")
        parser.ParseFile(file_path)