# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
"""Gitignore parser configured to work for edk2-pytool-library."""
from pathlib import Path
from os.path import dirname, abspath
import re
import os
import collections

"""Original file is from
https://github.com/mherrmann/gitignore_parser/blob/master/gitignore_parser.py
sha hash: 31407327e4a10d122632c5f03c7a705b010e5fbd

Original License:

MIT License

Copyright (c) 2018 Michael Herrmann
Copyright (c) 2015 Steve Cook

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def handle_negation(file_path, rules):
    """Allows `matched` value override if negation is true.

    Otherwise `matched` cannot be overwritten with an exception.
    Used for ensuring rules with ! will override a previous true result back to false.
    """
    matched = False
    for rule in rules:
        if rule.match(file_path):
            if rule.negation:
                matched = False
            else:
                matched = True
    return matched


def parse_gitignore_file(full_path, base_dir=None):
    """Parse a gitignore file."""
    if base_dir is None:
        base_dir = dirname(full_path)
    with open(full_path) as ignore_file:
        lines = ignore_file.readlines()
    return parse_gitignore_lines(lines, full_path, base_dir)


def parse_gitignore_lines(lines: list, full_path: str, base_dir: str):
    """Parse a list of lines matching gitignore syntax."""
    counter = 0
    rules = []
    for line in lines:
        counter += 1
        line = line.rstrip('\n')
        rule = rule_from_pattern(line, abspath(base_dir),
                                 source=(full_path, counter))
        if rule:
            rules.append(rule)
    return lambda file_path: handle_negation(file_path, rules)


def rule_from_pattern(pattern, base_path=None, source=None):
    """Generates an IgnoreRule object from a pattern.

    Take a .gitignore match pattern, such as "*.py[cod]" or "**/*.bak",
    and return an IgnoreRule suitable for matching against files and
    directories. Patterns which do not match files, such as comments
    and blank lines, will return None.
    Because git allows for nested .gitignore files, a base_path value
    is required for correct behavior. The base path should be absolute.
    """
    if base_path and base_path != abspath(base_path):
        raise ValueError('base_path must be absolute')
    # Store the exact pattern for our repr and string functions
    orig_pattern = pattern
    # Early returns follow
    # Discard comments and seperators
    if pattern.strip() == '' or pattern[0] == '#':
        return
    # Discard anything with more than two consecutive asterisks
    if pattern.find('***') > -1:
        return
    # Strip leading bang before examining double asterisks
    if pattern[0] == '!':
        negation = True
        pattern = pattern[1:]
    else:
        negation = False
    # Discard anything with invalid double-asterisks -- they can appear
    # at the start or the end, or be surrounded by slashes
    for m in re.finditer(r'\*\*', pattern):
        start_index = m.start()
        if (start_index != 0 and start_index != len(pattern) - 2
            and (pattern[start_index - 1] != '/' or pattern[start_index + 2] != '/')): # noqa
            return

    # Special-casing '/', which doesn't match any files or directories
    if pattern.rstrip() == '/':
        return

    directory_only = pattern[-1] == '/'
    # A slash is a sign that we're tied to the base_path of our rule
    # set.
    anchored = '/' in pattern[:-1]
    if pattern[0] == '/':
        pattern = pattern[1:]
    if pattern[0] == '*' and pattern[1] == '*':
        pattern = pattern[2:]
        anchored = False
    if pattern[0] == '/':
        pattern = pattern[1:]
    if pattern[-1] == '/':
        pattern = pattern[:-1]
    regex = fnmatch_pathname_to_regex(
        pattern
    )
    if anchored:
        # DeprecationWarning: Flags not at the start of the expression
        # Must ensure (?ms) is at the front of the regex, so we can no
        # longer put ^ in the beginning of a regex string.
        # OLD example: ^(?ms)\.eggs$
        # NEW Example: (?ms)^\.eggs$
        # regex = ''.join(['^', regex])
        regex = regex[:5] + '^' + regex[5:]
    return IgnoreRule(
        pattern=orig_pattern,
        regex=regex,
        negation=negation,
        directory_only=directory_only,
        anchored=anchored,
        base_path=Path(base_path) if base_path else None,
        source=source
    )


whitespace_re = re.compile(r'(\\ )+$')

IGNORE_RULE_FIELDS = [
    'pattern', 'regex',  # Basic values
    'negation', 'directory_only', 'anchored',  # Behavior flags
    'base_path',  # Meaningful for gitignore-style behavior
    'source'  # (file, line) tuple for reporting
]


class IgnoreRule(collections.namedtuple('IgnoreRule_', IGNORE_RULE_FIELDS)):
    """Class representing a single rule parsed from a .ignore file."""
    def __str__(self):
        """String representation (user friendly) of the rule."""
        return self.pattern

    def __repr__(self):
        """String representation (developer friendly) of the rule."""
        return ''.join(['IgnoreRule(\'', self.pattern, '\')'])

    def match(self, abs_path):
        """Returns True or False if the path matches the rule."""
        matched = False
        if self.base_path:
            rel_path = str(Path(abs_path).relative_to(self.base_path))
        else:
            rel_path = str(Path(abs_path))
        if rel_path.startswith('./'):
            rel_path = rel_path[2:]
        if re.search(self.regex, rel_path):
            matched = True
        return matched


# Frustratingly, python's fnmatch doesn't provide the FNM_PATHNAME
# option that .gitignore's behavior depends on.
def fnmatch_pathname_to_regex(pattern):
    """Implements fnmatch style-behavior, as though with FNM_PATHNAME flagged.

    WARNING: the path seperator will not match shell-style '*' and '.' wildcards.
    """
    i, n = 0, len(pattern)

    seps = [re.escape(os.sep)]
    if os.altsep is not None:
        seps.append(re.escape(os.altsep))
    seps_group = r'[{}]'.format(''.join(seps))
    nonsep = r'[^{}]'.format(''.join(seps))

    res = []
    while i < n:
        c = pattern[i]
        i += 1
        if c == '*':
            try:
                if pattern[i] == '*':
                    i += 1
                    res.append('.*')
                    if pattern[i] == '/':
                        i += 1
                        res.append(''.join([seps_group, '?']))
                else:
                    res.append(''.join([nonsep, '*']))
            except IndexError:
                res.append(''.join([nonsep, '*']))
        elif c == '?':
            res.append(nonsep)
        elif c == '/':
            res.append(seps_group)
        elif c == '[':
            j = i
            if j < n and pattern[j] == '!':
                j += 1
            if j < n and pattern[j] == ']':
                j += 1
            while j < n and pattern[j] != ']':
                j += 1
            if j >= n:
                res.append('\\[')
            else:
                stuff = pattern[i:j].replace('\\', '\\\\')
                i = j + 1
                if stuff[0] == '!':
                    stuff = ''.join(['^', stuff[1:]])
                elif stuff[0] == '^':
                    stuff = ''.join('\\' + stuff)
                res.append('[{}]'.format(stuff))
        else:
            res.append(re.escape(c))
    res.insert(0, '(?ms)')
    res.append('$')
    return ''.join(res)
