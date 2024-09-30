## @file override_parser.py
# Contains classes to help with the parsing of INF files that
# may contain OVERRIDE information.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Contains classes to help with parsing INF files that may contain OVERRIDE information."""

import datetime
import os
from typing import Optional

FORMAT_VERSION_1 = (1, 4)  # Version 1: #OVERRIDE : VERSION | PATH_TO_MODULE | HASH | YYYY-MM-DDThh-mm-ss


class OpParseError(Exception):
    """Class representing OpParseError types."""

    PE_VER = "VERSION"
    PE_PATH = "PATH"
    PE_HASH = "HASH"
    PE_DATE = "DATE"

    def __init__(self, my_type: str) -> "OpParseError":
        """Verifies type is a valid OpParseError type."""
        if my_type not in (OpParseError.PE_VER, OpParseError.PE_PATH, OpParseError.PE_HASH, OpParseError.PE_DATE):
            raise ValueError("Unknown type '%s'" % my_type)
        self.type = my_type

    def __str__(self) -> str:
        """String representation of the OpParseError type."""
        return repr(self.type)


class OverrideParser(object):
    """OverrideParser is a simple file parser for .inf files.

    OverrideParser must contain OVERRIDE data (i.e. overriding other .infs).
    Creating the object can be done by passing either a valid file path
    or a string containing the contents of an .inf file.

    Will raise an exception if the file doesn't exist or if the contents
    do not contain any OVERRIDE data.

    NOTE: There is an argument to be made that this class should actually be
          a subclass of InfParser, however, the InfParser is looking for far
          more details and has a much higher overhead. During a parser refactor,
          this should be considered.

    NOTE: There is a pattern used here where the object parses during
          instantiation. This pattern does not necessarily match the other
          parsers. The pros and cons of this should also be weighed during
          any parser refactor.
    """

    def __init__(self, file_path: Optional[str] = None, inf_contents: Optional[str] = None) -> "OverrideParser":
        """Inits and parses either a file or already parsed contents.

        Args:
            file_path: Path to an INF file
            inf_contents: Parsed lines as a string

        NOTE: Either file_path or inf_contents must be provided.
        """
        super(OverrideParser, self).__init__()

        # Make sure that at least some data is provided.
        if file_path is None and inf_contents is None:
            raise ValueError("file_path or inf_contents is required.")
        # Make sure not too much data is provided.
        if file_path is not None and inf_contents is not None:
            raise ValueError("Only provide file_path or inf_contents. (%s, %s)" % (file_path, inf_contents))
        # If a file path was provided, make sure it exists.
        if file_path is not None:
            if not os.path.isfile(file_path):
                raise ValueError("File path '%s' does not exist." % file_path)

        self.file_path = os.path.abspath(file_path) if file_path is not None else "String Buffer"

        # Set up the contents for parsing.
        parse_contents = inf_contents
        if file_path is not None:
            with open(file_path, "r") as file:
                parse_contents = file.read()
        if not parse_contents:
            raise ValueError("Failed to read contents of file '%s'." % self.file_path)

        self.override_lines = self.get_override_lines(parse_contents)

        # If no override lines were found, we're basically done here.
        if not self.override_lines:
            raise ValueError("File '%s' did not contain any override lines." % self.file_path)

        self.overrides = []
        for override_line in self.override_lines:
            try:
                self.overrides.append(self.parse_override_line(override_line["line"]))
            except OpParseError as pe:
                raise ValueError(
                    "Parse error '%s' occurred while processing line %d of '%s'."
                    % (pe, override_line["lineno"], override_line["line"])
                )

    @staticmethod
    def get_override_lines(parse_contents: str) -> list:
        """Parses contents and returns only lines that start with #OVERRIDE.

        Returns:
            (list[str]): lines starting with #OVERRIDE
        """
        parse_lines = parse_contents.split("\n")
        result = []

        for i in range(len(parse_lines)):
            if parse_lines[i].strip().upper().startswith("#OVERRIDE"):
                result.append({"lineno": i + 1, "line": parse_lines[i].strip()})

        return result

    @staticmethod
    def parse_override_line(line_contents: str) -> dict:
        """Parses an override_line.

        Args:
            line_contents (str): a line that starts with #OVERRIDE

        Returns:
            (dict): Key/Value pairs including version, original_path, current_hash, datetime

        Raises:
            (OpParseError): Failed to parse one of the keys
        """
        result = {}

        # Split the override string into pieces.
        # First the #OVERRIDE, which is separated by a :.
        # Then everything else by |.
        line_parts = line_contents.split(":")
        line_parts = [part.strip() for part in line_parts[1].split("|")]

        # Step 1: Check version and number of blocks in this entry
        try:
            result["version"] = int(line_parts[0])
        except ValueError:
            raise OpParseError(OpParseError.PE_VER)

        # Verify this is a known version and has valid number of entries
        if not ((result["version"] == FORMAT_VERSION_1[0]) and (len(line_parts) == FORMAT_VERSION_1[1])):
            raise OpParseError(OpParseError.PE_VER)

        # Step 2: Process the path to overridden module
        # Normalize the path to support different slashes.
        result["original_path"] = os.path.normpath(line_parts[1])

        # Step 3: Grep hash entry
        result["current_hash"] = line_parts[2]

        # Step 4: Parse the time of hash generation
        try:
            result["datetime"] = datetime.datetime.strptime(line_parts[3], "%Y-%m-%dT%H-%M-%S")
        except ValueError:
            raise OpParseError(OpParseError.PE_DATE)

        return result
