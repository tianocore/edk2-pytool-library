# @file gitignore_parser_test.py
# unit test for gitignore_parser module.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import tempfile
import unittest
from pathlib import Path

import edk2toollib.gitignore_parser as gitignore_parser


def BuildGitIgnore(root):
    path = os.path.join(root, ".gitignore")
    with open(path, "w") as gitignore:
        gitignore.write("/Build/\n")
        gitignore.write("./Logs/\n")
        gitignore.write("**/Test/\n")
        gitignore.write(".DS_Store\n")
        gitignore.write("*_extdep/\n")
        gitignore.write("*.pyc\n")
        gitignore.write("__pycache__/\n")
        gitignore.write("tags/\n")
        gitignore.write(".vscode/\n")
        gitignore.write("*.bak\n")
        gitignore.write("BuildConfig.conf\n")
        gitignore.write(" \n")
        gitignore.write("*.exe\n")
        gitignore.write("!important.exe\n")
        gitignore.write("/BaseTools/BaseToolsBuild/\n")
        gitignore.write("/docs/**/*.txt\n")
        gitignore.write("/reader/*\n")
        gitignore.write("out?.log\n")
        gitignore.write("log[0-9].txt\n")
        gitignore.write("log0[!a-z].txt\n")
    return path


class GitIgnoreParserTest(unittest.TestCase):

    def test_gitignoreparser_filter(self):
        '''Ensure the gitignore parser filters files and folders correctly per
        what is specified in the parsed .gitignore file.
        '''
        with tempfile.TemporaryDirectory() as root:
            root = Path(root).resolve()
            gitignore_path = BuildGitIgnore(root)
            rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

            # Test a rule which specifies that a specific folder at root is
            # correctly filtered.

            # Example line in a .gitignore
            # /Build/
            self.assertTrue(rule_tester(root / "Build"))
            self.assertFalse(rule_tester(root / "T" / "Build"))

            # Test a rule which specifies that a specific folder is not
            # filtered, but the contents of the folder is filtered

            # Example ine in a .gitignore
            # /reader/*
            self.assertFalse(rule_tester(root / "reader"))
            self.assertTrue(rule_tester(root / "reader" / "testing.txt"))

            # Test a rule which specifies that a folder at any depth from the
            # root is correctly filtered.

            # Example line in a .gitignore
            # **/Test/
            self.assertTrue(rule_tester(root / "Test"))
            self.assertTrue(rule_tester(root / "T" / "Test"))

            # Test a rule which specifies that a folder containing a specific
            # string at any depth is correctly filtered.

            # Example line in a .gitignore
            # *_extdep
            self.assertTrue(rule_tester(root / 'test_extdep'))
            self.assertTrue(rule_tester(root / 'T' / 'test_extdep'))

            # Test a rule which specifies that a file of a specific type at any
            # depth is correctly filtered.

            # Example line in a .gitignore
            # .DS_Store
            self.assertTrue(rule_tester(root / "file.DS_Store"))
            self.assertTrue(rule_tester(root / "T" / "file.DS_Store"))

            # Test a rule which specifies an exception for a previous rule is
            # correctly filtered.

            # Example line in a .gitignore
            # *.exe
            # !important.exe
            self.assertTrue(rule_tester(root / 'test.exe'))
            self.assertTrue(rule_tester(root / 'T' / 'test.exe'))
            self.assertFalse(rule_tester(root / 'important.exe'))
            self.assertFalse(rule_tester(root / 'T' / 'important.exe'))

            # Test a rule which specifies a file type in any directory under a
            # specific folder are correctly filtered.

            # Example line in a .gitignore
            # /docs/**/*.txt
            self.assertTrue(rule_tester(root / 'docs' / 'notes.txt'))
            self.assertFalse(rule_tester(root / 'docs' / 'Readme.md'))
            self.assertTrue(rule_tester(root / 'docs' / 'developing' / 'notes.txt'))
            self.assertFalse(rule_tester(root / 'docs' / 'developing' / 'Readme.md'))

            # Test a rule which specifies a file with a specific naming convention be
            # correctly filtered

            # Example line in a .gitignore
            # out?.log

            self.assertTrue(rule_tester(root / 'out1.log'))
            self.assertTrue(rule_tester(root / 'outF.log'))
            self.assertFalse(rule_tester(root / 'out11.log'))

            # log[0-9].txt
            self.assertTrue(rule_tester(root / 'log1.txt'))
            self.assertFalse(rule_tester(root / 'logF.txt'))
            self.assertFalse(rule_tester(root / 'log11.txt'))

            # log0[!a-z].txt
            self.assertTrue(rule_tester(root / 'log01.txt'))
            self.assertFalse(rule_tester(root / 'log0a.txt'))
            self.assertTrue(rule_tester(root / 'log0A.txt'))

    def test_rule_from_pattern(self):

        # Test bad basepath
        self.assertRaises(ValueError, gitignore_parser.rule_from_pattern, "", "Test")

        # Test ignoring comments, line separators, and incorrect astrick count
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(gitignore_parser.rule_from_pattern("# Comment", root))
            self.assertIsNone(gitignore_parser.rule_from_pattern(" ", root))
            self.assertIsNone(gitignore_parser.rule_from_pattern("***", root))

def test_ignore_no_extensions(tmp_path):
        """Tests that files without an extension can be ignored."""
        root = tmp_path.resolve()
        gitignore_path = root / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("*\n")
            f.write("!*.*\n")
            f.write("!*/\n")

        rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

        assert rule_tester(root / "File.txt") is False
        assert rule_tester(root / "executable") is True

        assert rule_tester(root / "files" / "file.txt") is False
        assert rule_tester(root / "bins" / "run_me") is True

def test_pound_in_filename(tmp_path):
    """Tests that a # symbol is escaped if prefixed with a \\."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, 'w') as f:
        f.write("#file.txt\n")
        f.write("\\#file.txt\n" )

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

    assert rule_tester(root / "file.txt") is False
    assert rule_tester(root / "#file.txt") is True

def test_trailing_whitespace(tmp_path):
    """Tests that trailing whitespace is properly ignored.

    Taken somewhat from "Test_trailingspaces" test from upstream
    """
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, 'w') as f:
        f.write('file1 \n')
        f.write('file2\\  \n')
        f.write('file3 \\  \n')
        f.write('file4\\ \\ \\ ')

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

    assert rule_tester(root / "file1") is True

    assert rule_tester(root / "file2 ") is True
    assert rule_tester(root / "file2") is False

    assert rule_tester(root / "file3  ") is True
    assert rule_tester(root / "file3 ") is False
    assert rule_tester(root / "file3") is False

    assert rule_tester(root / "file4   ") is True
    assert rule_tester(root / "file4  ") is False
    assert rule_tester(root / "file4 ") is False
    assert rule_tester(root / "file4") is False
