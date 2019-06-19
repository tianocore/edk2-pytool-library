##
# junit_report_format
# This module contains support for Outputting Junit test results xml.
#
# Used to support CI/CD and exporting test results for other tools.
# This does test report generation without being a test runner.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import time


class JunitReportError(object):
    def __init__(self, type, msg):
        self.Message = msg
        self.Type = type


class JunitReportFailure(object):
    def __init__(self, type, msg):
        self.Message = msg
        self.Type = type

##
# Test Case class
#
##


class JunitReportTestCase(object):
    NEW = 1
    SKIPPED = 2
    FAILED = 3
    ERROR = 4
    SUCCESS = 5

    def __init__(self, Name, ClassName):
        self.Name = Name
        self.ClassName = ClassName
        self.Time = 0
        self.Status = JunitReportTestCase.NEW

        self.FailureMsg = None
        self.ErrorMsg = None
        self._TestSuite = None
        self.StdErr = ""
        self.StdOut = ""
        self._StartTime = time.time()

    def SetFailed(self, Msg, Type):
        if(self.Status != JunitReportTestCase.NEW):
            raise Exception("Can't Set to failed.  State must be in NEW")
        self.Time = time.time() - self._StartTime
        self.Status = JunitReportTestCase.FAILED
        self.FailureMsg = JunitReportFailure(Type, Msg)

    def SetError(self, Msg, Type):
        if(self.Status != JunitReportTestCase.NEW):
            raise Exception("Can't Set to error.  State must be in NEW")
        self.Time = time.time() - self._StartTime
        self.Status = JunitReportTestCase.ERROR
        self.ErrorMsg = JunitReportError(Type, Msg)

    def SetSuccess(self):
        if(self.Status != JunitReportTestCase.NEW):
            raise Exception("Can't Set to success.  State must be in NEW")
        self.Status = JunitReportTestCase.SUCCESS
        self.Time = time.time() - self._StartTime

    def SetSkipped(self):
        if(self.Status != JunitReportTestCase.NEW):
            raise Exception("Can't Set to skipped.  State must be in NEW")
        self.Status = JunitReportTestCase.SKIPPED
        self.Time = time.time() - self._StartTime

    def LogStdOut(self, msg):
        self.StdOut += msg.strip() + "\n "

    def LogStdError(self, msg):
        self.StdErr += msg.strip() + "\n "

    def Output(self, outstream):
        outstream.write('<testcase classname="{0}" name="{1}" time="{2}">'.format(self.ClassName, self.Name, self.Time))
        if self.Status == JunitReportTestCase.SKIPPED:
            outstream.write('<skipped />')
        elif self.Status == JunitReportTestCase.FAILED:
            outstream.write('<failure message="{0}" type="{1}" />'.format(self.FailureMsg.Message,
                                                                          self.FailureMsg.Type))
        elif self.Status == JunitReportTestCase.ERROR:
            outstream.write('<error message="{0}" type="{1}" />'.format(self.ErrorMsg.Message, self.ErrorMsg.Type))
        elif self.Status != JunitReportTestCase.SUCCESS:
            raise Exception("Can't output a testcase {0}.{1} in invalid state {2}".format(self.ClassName,
                                                                                          self.Name, self.Status))

        outstream.write('<system-out>' + self.StdOut + '</system-out>')
        outstream.write('<system-err>' + self.StdErr + '</system-err>')
        outstream.write('</testcase>')


##
# Test Suite class.  Create new suites by using the JunitTestReport Object
#
#
##
class JunitReportTestSuite(object):
    def __init__(self, Name, Package, Id):
        self.Name = Name
        self.Package = Package
        self.TestId = Id
        self.TestCases = []

    def create_new_testcase(self, name, classname):
        tc = JunitReportTestCase(name, classname)
        self.TestCases.append(tc)
        tc._TestSuite = self
        return tc

    def Output(self, outstream):
        Errors = 0
        Failures = 0
        Skipped = 0
        Tests = len(self.TestCases)

        for a in self.TestCases:
            if(a.Status == JunitReportTestCase.FAILED):
                Failures += 1
            elif(a.Status == JunitReportTestCase.ERROR):
                Errors += 1
            elif(a.Status == JunitReportTestCase.SKIPPED):
                Skipped += 1

        outstream.write('<testsuite id="{0}" name="{1}" package="{2}" errors="{3}" tests="{4}" '
                        'failures="{5}" skipped="{6}">'.format(self.TestId, self.Name, self.Package,
                                                               Errors, Tests, Failures, Skipped))

        for a in self.TestCases:
            a.Output(outstream)

        outstream.write('</testsuite>')

##
# Test Report.  Top level object test reporting.
#
#
##


class JunitTestReport(object):
    def __init__(self):
        self.TestSuites = []

    def create_new_testsuite(self, name, package):
        id = len(self.TestSuites)
        ts = JunitReportTestSuite(name, package, id)
        self.TestSuites.append(ts)
        return ts

    def Output(self, filepath):
        f = open(filepath, "w")
        f.write('')
        f.write('<?xml version="1.0" encoding="UTF-8"?>')
        f.write('<testsuites>')
        for a in self.TestSuites:
            a.Output(f)
        f.write('</testsuites>')
        f.close()
