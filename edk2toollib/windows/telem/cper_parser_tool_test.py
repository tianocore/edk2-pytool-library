# @file test_signtool_signer.py
# This contains unit tests for the cper parser
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
from edk2toollib.windows.telem import cper_parser_tool as parser
from edk2toolext.windows.telem.testdata import TestData, TestDataParsed


class cper_parser_tool_test(unittest.TestCase):

    def test_section_count(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            self.assertEqual(rec.GetSectionCount(), int(TestDataParsed[counter][0]))
            counter += 1

    def test_severity(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            self.assertEqual(rec.GetErrorSeverity(), TestDataParsed[counter][1])
            counter += 1

    def test_record_length(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            self.assertEqual(rec.GetRecordLength(), int(TestDataParsed[counter][2]))
            counter += 1

    def test_timestamp(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            self.assertEqual(rec.GetTimestamp(), TestDataParsed[counter][3])
            counter += 1

    def test_platform_id(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            self.assertEqual(rec.GetPlatformId(), TestDataParsed[counter][4])
            counter += 1

    def test_partition_id(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            self.assertEqual(rec.GetPartitionId(), TestDataParsed[counter][5])
            counter += 1

    def test_creator_id(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            self.assertEqual(rec.GetCreatorId(), TestDataParsed[counter][6])
            counter += 1

    def test_record_id(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            self.assertEqual(rec.GetRecordId(), TestDataParsed[counter][7])
            counter += 1

    def test_flags(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            flaglist = rec.GetFlags()
            flaglisttestdata = TestDataParsed[counter][8].split(',')
            for idx in range(len(flaglist)):
                self.assertEqual(flaglist[idx], flaglisttestdata[idx])
            counter += 1

    def test_sections_length(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            sectionslength = rec.GetSectionsLength()
            sectionslengthtestdata = TestDataParsed[counter][9].split(',')
            for idx in range(len(sectionslength)):
                self.assertEqual(sectionslength[idx], int(sectionslengthtestdata[idx]))
            counter += 1

    def test_sections_type(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            sectionstype = rec.GetSectionsType()
            sectionstypetestdata = TestDataParsed[counter][11].split(',')
            for idx in range(len(sectionstype)):
                self.assertEqual(sectionstype[idx], sectionstypetestdata[idx])
            counter += 1

    def test_sections_fru_id(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            sectionsfruid = rec.GetSectionsFruId()
            sectionsfruidtestdata = TestDataParsed[counter][12].split(',')
            for idx in range(len(sectionsfruid)):
                self.assertEqual(sectionsfruid[idx], sectionsfruidtestdata[idx])
            counter += 1

    def test_sections_severity(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            sectionsseverity = rec.GetSectionsSeverity()
            sectionsseveritytestdata = TestDataParsed[counter][13].split(',')
            for idx in range(len(sectionsseverity)):
                self.assertEqual(sectionsseverity[idx], sectionsseveritytestdata[idx])
            counter += 1

    @unittest.skip("unimplemented")
    def test_sections_fru_text(self):
        counter = 1
        for data in TestData:
            rec = parser.CPER(data)
            sectionsfrustring = rec.GetSectionsFruString()
            sectionsfrustringtestdata = TestDataParsed[counter][14].split(',')
            for idx in range(len(sectionsfrustring)):
                self.assertEqual(sectionsfrustring[idx], sectionsfrustringtestdata[idx])
            counter += 1


if __name__ == '__main__':
    unittest.main()
