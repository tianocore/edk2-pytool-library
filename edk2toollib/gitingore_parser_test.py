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

    def test_filter_directory_at_base(self):
        '''
        Ensure the gitignore parser works properly when a rule specifies that
        a folder at the base of the directory is filtered.

        Example: /Build/
        '''
        with tempfile.TemporaryDirectory() as root:

            gitignore_path = BuildGitIgnore(root)
            rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

            # Windows
            self.assertTrue(rule_tester(f'{root}\\Build'))
            self.assertFalse(rule_tester(f'{root}\\T\\Build'))

            # Linux
            self.assertTrue(rule_tester(f'{root}/Build'))
            self.assertFalse(rule_tester(f'{root}/T\\Build'))

    def test_filter_directory_at_any_level(self):
        '''
        Ensure the gitignore parser works properly when a rule specifies that
        a folder at any depth from the root directory is filtered.

        Example: **/Test/
        '''
        with tempfile.TemporaryDirectory() as root:

            gitignore_path = BuildGitIgnore(root)
            rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

            # Windows
            self.assertTrue(rule_tester(f'{root}\\Test'))
            self.assertTrue(rule_tester(f'{root}\\T\\Test'))

            # Linux
            self.assertTrue(rule_tester(f'{root}/Test'))
            self.assertTrue(rule_tester(f'{root}/T/Test'))

    def test_filter_specific_folder_name(self):
        '''
        Ensure the gitignore parser works properly when a rule specifies that
        a folder that contains a certain string be filtered

        Example: *_extdep
        '''
        with tempfile.TemporaryDirectory() as root:

            gitignore_path = BuildGitIgnore(root)
            rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

            # Windows
            self.assertTrue(rule_tester(f'{root}\\test_extdep'))
            self.assertTrue(rule_tester(f'{root}\\T\\test_extdep'))

            # Linux
            self.assertTrue(rule_tester(f'{root}/test_extdep'))
            self.assertTrue(rule_tester(f'{root}/T/test_extdep'))

    def test_filter_specific_file_type(self):
        '''
        Ensure the gitignore parser works properly when a rule specifies that
        a file of a specific type  be filtered

        Example: *.DS_Store
        '''
        with tempfile.TemporaryDirectory() as root:

            gitignore_path = BuildGitIgnore(root)
            rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

            # Windows
            self.assertTrue(rule_tester(f'{root}\\file.DS_Store'))
            self.assertTrue(rule_tester(f'{root}\\T\\file.DS_Store'))

            # Linux
            self.assertTrue(rule_tester(f'{root}/file.DS_Store'))
            self.assertTrue(rule_tester(f'{root}/T/file.DS_Store'))