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
"""Module for outputting Junit test results to xml.

Used to support CI/CD and exporting test results for other tools.
This does test report generation without being a test runner.
"""
import time
from xml.sax.saxutils import escape


class JunitReportError(object):
    """Object representing a Test Error."""
    def __init__(self, type, msg):
        """Init the type of error."""
        self.Message = escape(msg.strip(), {'"': "&quot;"})
        self.Type = escape(type.strip(), {'"': "&quot;"})


class JunitReportFailure(object):
    """Object representing a Test Failure."""
    def __init__(self, type, msg):
        """Init the type of Failure."""
        self.Message = escape(msg.strip(), {'"': "&quot;"})
        self.Type = escape(type.strip(), {'"': "&quot;"})


class JunitReportTestCase(object):
    """Object representing a single test case."""
    NEW = 1
    SKIPPED = 2
    FAILED = 3
    ERROR = 4
    SUCCESS = 5

    def __init__(self, Name, ClassName):
        """Init a Test case with it's name and class name."""
        self.Name = escape(Name.strip(), {'"': "&quot;"})
        self.ClassName = escape(ClassName.strip(), {'"': "&quot;"})
        self.Time = 0
        self.Status = JunitReportTestCase.NEW

        self.FailureMsg = None
        self.ErrorMsg = None
        self._TestSuite = None
        self.StdErr = ""
        self.StdOut = ""
        self._StartTime = time.time()

    def SetFailed(self, Msg, Type):
        """Sets internal state if the test failed."""
        if (self.Status != JunitReportTestCase.NEW):
            raise Exception("Can't Set to failed.  State must be in NEW")
        self.Time = time.time() - self._StartTime
        self.Status = JunitReportTestCase.FAILED
        self.FailureMsg = JunitReportFailure(Type, Msg)

    def SetError(self, Msg, Type):
        """Set internal state if the test had an error."""
        if (self.Status != JunitReportTestCase.NEW):
            raise Exception("Can't Set to error.  State must be in NEW")
        self.Time = time.time() - self._StartTime
        self.Status = JunitReportTestCase.ERROR
        self.ErrorMsg = JunitReportError(Type, Msg)

    def SetSuccess(self):
        """Set internal state if the test passed."""
        if (self.Status != JunitReportTestCase.NEW):
            raise Exception("Can't Set to success.  State must be in NEW")
        self.Status = JunitReportTestCase.SUCCESS
        self.Time = time.time() - self._StartTime

    def SetSkipped(self):
        """Set internal state if the test was skipped."""
        if (self.Status != JunitReportTestCase.NEW):
            raise Exception("Can't Set to skipped.  State must be in NEW")
        self.Status = JunitReportTestCase.SKIPPED
        self.Time = time.time() - self._StartTime

    def LogStdOut(self, msg):
        """Log to the standard out."""
        self.StdOut += escape(msg.strip()) + "\n "

    def LogStdError(self, msg):
        """Log to the standard err."""
        self.StdErr += escape(msg.strip()) + "\n "

    def Output(self, outstream):
        """Write the test result to the outstream."""
        outstream.write('<testcase classname="{0}" name="{1}" time="{2}">'.format(self.ClassName, self.Name, self.Time))
        if self.Status == JunitReportTestCase.SKIPPED:
            outstream.write('<skipped type="skipped">')
            outstream.write(self.StdOut)
            outstream.write('</skipped>')
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


class JunitReportTestSuite(object):
    """Object representing the overall test suite.

    Create new suites by using the JunitTestReport Object
    """
    def __init__(self, Name, Package, Id):
        """Initialize a new test suite."""
        self.Name = escape(Name.strip(), {'"': "&quot;"})
        self.Package = escape(Package.strip(), {'"': "&quot;"})
        self.TestId = Id
        self.TestCases = []

    def create_new_testcase(self, name, classname):
        """Create a new test case.

        Returns:
            (JunitReportTestCase): newly created test case
        """
        tc = JunitReportTestCase(name, classname)
        self.TestCases.append(tc)
        tc._TestSuite = self
        return tc

    def Output(self, outstream):
        """Output the test results to the stream."""
        Errors = 0
        Failures = 0
        Skipped = 0
        Tests = len(self.TestCases)

        for a in self.TestCases:
            if (a.Status == JunitReportTestCase.FAILED):
                Failures += 1
            elif (a.Status == JunitReportTestCase.ERROR):
                Errors += 1
            elif (a.Status == JunitReportTestCase.SKIPPED):
                Skipped += 1

        outstream.write('<testsuite id="{0}" name="{1}" package="{2}" errors="{3}" tests="{4}" '
                        'failures="{5}" skipped="{6}">'.format(self.TestId, self.Name, self.Package,
                                                               Errors, Tests, Failures, Skipped))

        for a in self.TestCases:
            a.Output(outstream)

        outstream.write('</testsuite>')


class JunitTestReport(object):
    """Object representing a Test Report.

    Top level object test reporting.
    """
    def __init__(self):
        """Init an empty test report."""
        self.TestSuites = []

    def create_new_testsuite(self, name, package):
        """Create a new test suite.

        Returns:
            (JunitReportTestSuite): newly created testsuite
        """
        id = len(self.TestSuites)
        ts = JunitReportTestSuite(name, package, id)
        self.TestSuites.append(ts)
        return ts

    def Output(self, filepath):
        """Write report to file."""
        f = open(filepath, "w")
        f.write('')
        f.write('<?xml version="1.0" encoding="UTF-8"?>')
        f.write('<testsuites>')
        for a in self.TestSuites:
            a.Output(f)
        f.write('</testsuites>')
        f.close()
