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
from pytest import skip


def BuildGitIgnore(root):
    """Builds a .gitignore file in the root directory."""
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
    """Tests for the gitignore parser."""

    def test_gitignoreparser_filter(self):
        """Ensure the gitignore parser filters files and folders correctly.

        This is per what is specified in the parsed .gitignore file.
        """
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
            self.assertTrue(rule_tester(root / "test_extdep"))
            self.assertTrue(rule_tester(root / "T" / "test_extdep"))

            # Test a rule which specifies that a file of a specific type at any
            # depth is correctly filtered.

            # Example line in a .gitignore
            # .DS_Store
            self.assertTrue(rule_tester(root / ".DS_Store"))
            self.assertTrue(rule_tester(root / "T" / ".DS_Store"))
            self.assertFalse(rule_tester(root / "file.DS_Store"))
            self.assertFalse(rule_tester(root / "T" / "file.DS_Store"))

            # Test a rule which specifies an exception for a previous rule is
            # correctly filtered.

            # Example line in a .gitignore
            # *.exe
            # !important.exe
            self.assertTrue(rule_tester(root / "test.exe"))
            self.assertTrue(rule_tester(root / "T" / "test.exe"))
            self.assertFalse(rule_tester(root / "important.exe"))
            self.assertFalse(rule_tester(root / "T" / "important.exe"))

            # Test a rule which specifies a file type in any directory under a
            # specific folder are correctly filtered.

            # Example line in a .gitignore
            # /docs/**/*.txt
            self.assertTrue(rule_tester(root / "docs" / "notes.txt"))
            self.assertFalse(rule_tester(root / "docs" / "Readme.md"))
            self.assertTrue(rule_tester(root / "docs" / "developing" / "notes.txt"))
            self.assertFalse(rule_tester(root / "docs" / "developing" / "Readme.md"))

            # Test a rule which specifies a file with a specific naming convention be
            # correctly filtered

            # Example line in a .gitignore
            # out?.log

            self.assertTrue(rule_tester(root / "out1.log"))
            self.assertTrue(rule_tester(root / "outF.log"))
            self.assertFalse(rule_tester(root / "out11.log"))

            # log[0-9].txt
            self.assertTrue(rule_tester(root / "log1.txt"))
            self.assertFalse(rule_tester(root / "logF.txt"))
            self.assertFalse(rule_tester(root / "log11.txt"))

            # log0[!a-z].txt
            self.assertTrue(rule_tester(root / "log01.txt"))
            self.assertFalse(rule_tester(root / "log0a.txt"))
            self.assertTrue(rule_tester(root / "log0A.txt"))

    def test_rule_from_pattern(self):
        """Tests general expected functionality of rule_from_pattern."""
        # Test bad basepath
        self.assertRaises(ValueError, gitignore_parser.rule_from_pattern, "", "Test")

        # Test ignoring comments, line separators, and incorrect astrick count
        with tempfile.TemporaryDirectory() as root:
            root = Path(root).resolve()
            self.assertIsNone(gitignore_parser.rule_from_pattern("# Comment", root))
            self.assertIsNone(gitignore_parser.rule_from_pattern(" ", root))


def test_ignore_no_extensions(tmp_path):
    """Tests that files without an extension can be ignored."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"
    with open(gitignore_path, "w") as f:
        f.write("*\n")
        f.write("!*.*\n")
        f.write("!*/\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

    assert rule_tester(root / "File.txt") is False
    assert rule_tester(root / "executable") is True

    assert rule_tester(root / "files" / "file.txt") is False
    assert rule_tester(root / "bins" / "run_me") is True


def test_pound_in_filename(tmp_path):
    r"""Tests that a # symbol is escaped if prefixed with a \\."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, "w") as f:
        f.write("#file.txt\n")
        f.write("\\#file.txt\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path)

    assert rule_tester(root / "file.txt") is False
    assert rule_tester(root / "#file.txt") is True


def test_test_trailingspace(tmp_path):
    """Tests that trailing spaces are not ignored."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, "w") as f:
        f.write("ignoretrailingspace \n")
        f.write("notignoredspace\\ \n")
        f.write("partiallyignoredspace\\  \n")
        f.write("partiallyignoredspace2 \\  \n")
        f.write("notignoredmultiplespace\\ \\ \\ ")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir="/home/tmp")

    assert rule_tester("/home/tmp/ignoretrailingspace") is True
    assert rule_tester("/home/tmp/ignoretrailingspace ") is False
    assert rule_tester("/home/tmp/partiallyignoredspace ") is True
    assert rule_tester("/home/tmp/partiallyignoredspace  ") is False
    assert rule_tester("/home/tmp/partiallyignoredspace") is False
    assert rule_tester("/home/tmp/partiallyignoredspace2  ") is True
    assert rule_tester("/home/tmp/partiallyignoredspace2   ") is False
    assert rule_tester("/home/tmp/partiallyignoredspace2 ") is False
    assert rule_tester("/home/tmp/partiallyignoredspace2") is False
    assert rule_tester("/home/tmp/notignoredspace ") is True
    assert rule_tester("/home/tmp/notignoredspace") is False
    assert rule_tester("/home/tmp/notignoredmultiplespace   ") is True
    assert rule_tester("/home/tmp/notignoredmultiplespace") is False


def test_slash_in_range_does_not_match_dirs(tmp_path):
    """Tests that a slash in a range does not match directories."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, "w") as f:
        f.write("abc[X-Z/]def\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir="/home/tmp")

    assert rule_tester("/home/tmp/abcdef") is False
    assert rule_tester("/home/tmp/abcXdef") is True
    assert rule_tester("/home/tmp/abcYdef") is True
    assert rule_tester("/home/tmp/abcZdef") is True
    assert rule_tester("/home/tmp/abc/def") is False
    assert rule_tester("/home/tmp/abcXYZdef") is False


def test_incomplete_filename(tmp_path):
    """Tests that an incomplete filename is not matched."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, "w") as f:
        f.write("o.py\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir="/home/tmp")

    assert rule_tester("/home/tmp/o.py") is True
    assert rule_tester("/home/tmp/foo.py") is False
    assert rule_tester("/home/tmp/o.pyc") is False
    assert rule_tester("/home/tmp/dir/o.py") is True
    assert rule_tester("/home/tmp/dir/foo.py") is False
    assert rule_tester("/home/tmp/dir/o.pyc") is False


def test_unrelated_path(tmp_path):
    """Tests that a path that is completely unrelated to another path works."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, "w") as f:
        f.write("*foo*\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir="/home/tmp")

    assert rule_tester("/home/tmp/foo") is True
    assert rule_tester("/some/other/dir") is False


def test_double_asterisks(tmp_path):
    """Test that double asterisk match any number of directories."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, "w") as f:
        f.write("foo/**/Bar\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir="/home/tmp")
    assert rule_tester("/home/tmp/foo/hello/Bar") is True
    assert rule_tester("/home/tmp/foo/world/Bar") is True
    assert rule_tester("/home/tmp/foo/Bar") is True
    assert rule_tester("/home/tmp/foo/BarBar") is False


def test_double_asterisk_without_slashes_handled_like_single_asterisk(tmp_path):
    """Test that a double asterisk without slashes is treated like a single asterisk."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, "w") as f:
        f.write("a/b**c/d\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir="/home/tmp")
    assert rule_tester("/home/tmp//a/bc/d") is True
    assert rule_tester("/home/tmp//a/bXc/d") is True
    assert rule_tester("/home/tmp//a/bbc/d") is True
    assert rule_tester("/home/tmp//a/bcc/d") is True
    assert rule_tester("/home/tmp//a/bcd") is False
    assert rule_tester("/home/tmp//a/b/c/d") is False
    assert rule_tester("/home/tmp//a/bb/cc/d") is False
    assert rule_tester("/home/tmp//a/bb/XX/cc/d") is False


def test_more_asterisks_handled_like_single_asterisk(tmp_path):
    """Test that multiple asterisk in a row are treated as a single astrick."""
    root = tmp_path.resolve()
    gitignore_path = root / ".gitignore"

    with open(gitignore_path, "w") as f:
        f.write("***a/b\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir="/home/tmp")
    assert rule_tester("/home/tmp//XYZa/b") is True
    assert rule_tester("/home/tmp//foo/a/b") is False

    gitignore_path = root / ".gitignore2"

    with open(gitignore_path, "w") as f:
        f.write("a/b***\n")

    rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir="/home/tmp")

    assert rule_tester("/home/tmp//a/bXYZ") is True
    assert rule_tester("/home/tmp//a/b/foo") is False


def test_symlink_to_another_directory():
    """Test the behavior of a symlink to another directory.

    The issue https://github.com/mherrmann/gitignore_parser/issues/29 describes how
    a symlink to another directory caused an exception to be raised during matching.
    This test ensures that the issue is now fixed.
    """
    with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as another_dir:
        project_dir = Path(project_dir).resolve()
        another_dir = Path(another_dir).resolve()
        gitignore_path = project_dir / ".gitignore"

        with open(gitignore_path, "w") as f:
            f.write("link\n")

        rule_tester = gitignore_parser.parse_gitignore_file(gitignore_path, base_dir=project_dir)

        # Create a symlink to another directory.
        link = project_dir / "link"
        target = another_dir / "target"
        try:
            link.symlink_to(target)
        except OSError:  # Missing permissions to do a symlink
            skip("Current user does not have permissions to perform symlink.")

        # Check the intended behavior according to
        # https://git-scm.com/docs/gitignore#_notes:
        # Symbolic links are not followed and are matched as if they were regular
        # files.
        assert rule_tester(link) is True
