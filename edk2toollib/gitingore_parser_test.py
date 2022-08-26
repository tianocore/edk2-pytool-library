# @file gitignore_parser.py
# unit test for gitignore_parser module.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import tempfile
import edk2toollib.gitignore_parser as gitignore_parser
import os


def BuildGitIgnore(root):
    path = os.path.join(root, ".gitignore")
    with open(path, "w") as gitignore:
        gitignore.write("/Build/\n")
        gitignore.write("**/Test/\n")
        gitignore.write(".DS_Store\n")
        gitignore.write("*_extdep/\n")
        gitignore.write("*.pyc\n")
        gitignore.write("__pycache__/\n")
        gitignore.write("tags/\n")
        gitignore.write(".vscode/\n")
        gitignore.write("*.bak\n")
        gitignore.write("BuildConfig.conf\n")
        gitignore.write("/BaseTools/BaseToolsBuild/\n")
        gitignore.write("*.exe")
    return path


class GitIgnoreParserTest(unittest.TestCase):

    def test_gitignoreparser_filter(self):
        '''
        Ensure the gitignore parser filters files and folders correctly per
        what is specified in the parsed .gitignore file.
        '''
        with tempfile.TemporaryDirectory() as root:

            gitignore_path = BuildGitIgnore(root)
            rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

            # Test a rule which specifies that a specific folder at root is
            # correctly filtered:

            # Example line in a .gitignore
            # /Build/
            self.assertTrue(rule_tester(os.path.join(root, "Build")))
            self.assertFalse(rule_tester(os.path.join(root, "T", "Build")))

            # Test a rule which specifies that a folder at any depth from the
            # root is correclty filtered:

            # Example line in a .gitignore
            # **/Test/
            self.assertTrue(rule_tester(os.path.join(root, "Test")))
            self.assertTrue(rule_tester(os.path.join(root, "T", "Test")))

            # Test a rule which specifies that a folder containing a specific
            # string at any depth is correctly filtered:

            # Example line in a .gitignore
            # *_extdep
            self.assertTrue(rule_tester(os.path.join(root, 'test_extdep')))
            self.assertTrue(rule_tester(os.path.join(root, 'T', 'test_extdep')))

            # Test a rule which specifies that a file of a specific type at any
            # depth is correctly filtered:
            self.assertTrue(rule_tester(os.path.join(root, "file.DS_Store")))
            self.assertTrue(rule_tester(os.path.join(root, "T", "file.DS_Store")))
