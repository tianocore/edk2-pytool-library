# @file junit_report_format_test.py
# Contains unit test routines for the junit_report_format module.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import tempfile
import shutil
import os
import xml.dom.minidom
from edk2toollib.log import junit_report_format


class TestJunitTestReport(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.test_dir = None
        super().__init__(*args, **kwargs)

    def prep_workspace(self):
        self.clean_workspace()
        self.test_dir = tempfile.mkdtemp()

    def clean_workspace(self):
        if self.test_dir is None:
            return
        if os.path.isdir(self.test_dir):
            shutil.rmtree(self.test_dir)
            self.test_dir = None

    def setUp(self):
        self.prep_workspace()

    def IsXmlFileValidXml(self, filepath):
        try:
            # this will fail in xml is invalid
            xml.dom.minidom.parse(filepath)
        except Exception as e:
            return (False, str(e))
        return (True, "")

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        self.clean_workspace()

    def test_valid(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.LogStdError("Message to standard error on failed case")
        jtc.SetFailed("Testing the failure path", "TEST")
        jtc2 = jts.create_new_testcase("test_success", "testcase.test.success")
        jtc2.LogStdOut("Message to standard out on success case")
        jtc2.SetSuccess()
        jtc3 = jts.create_new_testcase("test_skipped", "testcase.test.skipped")
        jtc3.SetSkipped()
        jtc4 = jts.create_new_testcase("test_error", "testcase.test.error")
        jtc4.SetError("Testing the error path", "exception")
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))

    def test_incomplete_test_results(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.LogStdError("Message to standard error on failed case")
        # Don't set State jtc.SetFailed("Testing the failure path", "TEST")
        f = os.path.join(self.test_dir, "testoutput.xml")
        with self.assertRaises(Exception):
            jr.Output(f)

    def test_xml_escape_in_testcase_name_classname_output(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase('test_failed"<', ">&'testcase.test.failed")
        jtc.SetSuccess()
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))
        Valid, Msg = self.IsXmlFileValidXml(f)
        self.assertTrue(Valid, msg=Msg)

    def test_xml_escape_in_testsuit_name_package_output(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite('testname"<', ">&'testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.SetSuccess()
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))
        Valid, Msg = self.IsXmlFileValidXml(f)
        self.assertTrue(Valid, msg=Msg)

    def test_xml_escape_in_std_error_output(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.LogStdError("Message to standard error on failed case with < char")
        jtc.SetSuccess()
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))
        Valid, Msg = self.IsXmlFileValidXml(f)
        self.assertTrue(Valid, msg=Msg)

    def test_xml_escape_in_std_out_output(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.LogStdOut("Message to \"standard out> ' on failed case with < & char")
        jtc.SetSuccess()
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))
        Valid, Msg = self.IsXmlFileValidXml(f)
        self.assertTrue(Valid, msg=Msg)

    def test_xml_escape_in_failed_msg(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.SetFailed("Message in failed case' with < & char", "Error")
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))
        Valid, Msg = self.IsXmlFileValidXml(f)
        self.assertTrue(Valid, msg=Msg)

    def test_xml_escape_in_failed_type(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.SetFailed("Message in failed case", "'Fa>ile\"d<")
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))
        Valid, Msg = self.IsXmlFileValidXml(f)
        self.assertTrue(Valid, msg=Msg)

    def test_xml_escape_in_error_msg(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_error", "testcase.test.error")
        jtc.SetError('Message in Error" case with < & char', "Error")
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))
        Valid, Msg = self.IsXmlFileValidXml(f)
        self.assertTrue(Valid, msg=Msg)

    def test_xml_escape_in_error_type(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_error", "testcase.test.error")
        jtc.SetError("Message in Error case", "Error&")
        f = os.path.join(self.test_dir, "testoutput.xml")
        jr.Output(f)
        self.assertTrue(os.path.isfile(f))
        Valid, Msg = self.IsXmlFileValidXml(f)
        self.assertTrue(Valid, msg=Msg)

    def test_set_success_after_set(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.SetFailed("Testing the failure path", "TEST")
        with self.assertRaises(Exception):
            jtc.SetSuccess()

    def test_set_skipped_after_set(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.SetFailed("Testing the failure path", "TEST")
        with self.assertRaises(Exception):
            jtc.SetSkipped()

    def test_set_error_after_set(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_failed", "testcase.test.failed")
        jtc.SetFailed("Testing the failure path", "TEST")
        with self.assertRaises(Exception):
            jtc.SetError("Bad test", "Bad Type")

    def test_set_failure_after_set(self):
        jr = junit_report_format.JunitTestReport()
        jts = jr.create_new_testsuite("testname", "testpackage")
        jtc = jts.create_new_testcase("test_success", "testcase.test.success")
        jtc.SetSuccess()
        with self.assertRaises(Exception):
            jtc.SetFailed("Testing the failure path", "TEST")
