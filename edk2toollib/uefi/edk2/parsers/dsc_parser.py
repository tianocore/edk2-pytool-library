# @file dsc_parser.py
# Code to help parse DSC files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Code to help parse DSC files."""
import logging
import os
import re

from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser


class DscParser(HashFileParser):
    """Object representing a parsed DSC file with a capability to parse.

    Attributes:
        SixMods (list): list of X64 Modules (the line in the file)
        SixModsEnhanced (list): Better parsed (in a dict) list of X64 Modules
        ThreeMods (list): list of IA32 Modules (the line in the file)
        ThreeModsEnhanced (list): Better parsed (in a dict) list of IA32 Modules
        OtherMods (list): list of other Mods that are not IA32, X64 specific
        Libs (list): list of Libs (the line in the file)
        LibsEnhanced (list): Better parsed (in a dict) list of Libs
        LibraryClassToInstanceDict (dict): Key (Library class) Value (Instance)
        Pcds (list): List of Pcds
    """
    SECTION_LIBRARY = "libraryclasses"
    SECTION_COMPONENT = "components"
    SECTION_REGEX = re.compile(r"\[(.*)\]")
    OVERRIDE_REGEX = re.compile(r"\<(.*)\>")

    def __init__(self):
        """Init an empty Parser."""
        super(DscParser, self).__init__('DscParser')
        self.SixMods = []
        self.SixModsEnhanced = []
        self.ThreeMods = []
        self.ThreeModsEnhanced = []
        self.OtherMods = []
        self.Libs = []
        self.Components = []
        self.LibsEnhanced = []
        self.ScopedLibraryDict = {}
        self.ParsingInBuildOption = 0
        self.LibraryClassToInstanceDict = {}
        self.Pcds = []
        self.PcdValueDict = {}
        self._no_fail_mode = False
        self._dsc_file_paths = set()  # This includes the full paths for every DSC that makes up the file

    def ReplacePcds(self, line: str) -> str:
        """Attempts to replace a token if it is a PCD token."""
        if line.startswith("!if"):
            tokens = line.split()
            if tokens[1] in self.PcdValueDict:
                line = line.replace(tokens[1], self.PcdValueDict[tokens[1]])
        return line

    def __ParseLine(self, Line, file_name=None, lineno=None):
        line_stripped = self.StripComment(Line).strip()
        if (len(line_stripped) < 1):
            return ("", [], None)
        line_stripped = self.ReplacePcds(line_stripped)
        line_resolved = self.ReplaceVariables(line_stripped)
        if (self.ProcessConditional(line_resolved)):
            # was a conditional
            # Other parser returns line_resolved, [].  Need to figure out which is right
            return ("", [], None)

        # not conditional keep processing

        # check if conditional is active
        if (not self.InActiveCode()):
            return ("", [], None)

        # check for include file and import lines from file
        if (line_resolved.strip().lower().startswith("!include")):
            # include line.
            tokens = line_resolved.split()
            include_file = tokens[1]
            sp = self.FindPath(include_file)
            if sp is None:
                raise FileNotFoundError(include_file)
            self.Logger.debug("Opening Include File %s" % sp)
            self._PushTargetFile(sp)
            lf = open(sp, "r")
            loc = lf.readlines()
            lf.close()
            return ("", loc, sp)

        # check for new section
        (IsNew, Section) = self.ParseNewSection(line_resolved)
        if (IsNew):
            self.CurrentSection = Section.upper()
            self.Logger.debug("New Section: %s" % self.CurrentSection)
            self.Logger.debug("FullSection: %s" % self.CurrentFullSection)
            return (line_resolved, [], None)

        # process line in x64 components
        if (self.CurrentFullSection.upper() == "COMPONENTS.X64"):
            if (self.ParsingInBuildOption > 0):
                if (".inf" in line_resolved.lower()):
                    p = self.ParseInfPathLib(line_resolved)
                    self.Libs.append(p)
                    self.Logger.debug("Found Library in a 64bit BuildOptions Section: %s" % p)
                elif "tokenspaceguid" in line_resolved.lower() and \
                        line_resolved.count('|') > 0 and line_resolved.count('.') > 0:
                    # should be a pcd statement
                    p = line_resolved.partition('|')
                    self.Pcds.append(p[0].strip())
                    self.PcdValueDict[p[0].strip()] = p[2].strip()
                    self.Logger.debug("Found a Pcd in a 64bit Module Override section: %s" % p[0].strip())
            else:
                if (".inf" in line_resolved.lower()):
                    p = self.ParseInfPathMod(line_resolved)
                    self.SixMods.append(p)
                    if file_name is not None and lineno is not None:
                        self.SixModsEnhanced.append({'file': os.path.normpath(file_name), 'lineno': lineno, 'data': p})
                    self.Logger.debug("Found 64bit Module: %s" % p)

            self.ParsingInBuildOption = self.ParsingInBuildOption + line_resolved.count("{")
            self.ParsingInBuildOption = self.ParsingInBuildOption - line_resolved.count("}")
            return (line_resolved, [], None)

        # process line in ia32 components
        elif (self.CurrentFullSection.upper() == "COMPONENTS.IA32"):
            if (self.ParsingInBuildOption > 0):
                if (".inf" in line_resolved.lower()):
                    p = self.ParseInfPathLib(line_resolved)
                    self.Libs.append(p)
                    if file_name is not None and lineno is not None:
                        self.LibsEnhanced.append({'file': os.path.normpath(file_name), 'lineno': lineno, 'data': p})
                    self.Logger.debug("Found Library in a 32bit BuildOptions Section: %s" % p)
                elif "tokenspaceguid" in line_resolved.lower() and \
                        line_resolved.count('|') > 0 and line_resolved.count('.') > 0:
                    # should be a pcd statement
                    p = line_resolved.partition('|')
                    self.Pcds.append(p[0].strip())
                    self.PcdValueDict[p[0].strip()] = p[2].strip()
                    self.Logger.debug("Found a Pcd in a 32bit Module Override section: %s" % p[0].strip())

            else:
                if (".inf" in line_resolved.lower()):
                    p = self.ParseInfPathMod(line_resolved)
                    self.ThreeMods.append(p)
                    if file_name is not None and lineno is not None:
                        self.ThreeModsEnhanced.append({'file': os.path.normpath(file_name),
                                                       'lineno': lineno, 'data': p})
                    self.Logger.debug("Found 32bit Module: %s" % p)

            self.ParsingInBuildOption = self.ParsingInBuildOption + line_resolved.count("{")
            self.ParsingInBuildOption = self.ParsingInBuildOption - line_resolved.count("}")
            return (line_resolved, [], None)

        # process line in other components
        elif ("COMPONENTS" in self.CurrentFullSection.upper()):
            if (self.ParsingInBuildOption > 0):
                if (".inf" in line_resolved.lower()):
                    p = self.ParseInfPathLib(line_resolved)
                    self.Libs.append(p)
                    self.Logger.debug("Found Library in a BuildOptions Section: %s" % p)
                elif "tokenspaceguid" in line_resolved.lower() and \
                        line_resolved.count('|') > 0 and line_resolved.count('.') > 0:
                    # should be a pcd statement
                    p = line_resolved.partition('|')
                    self.Pcds.append(p[0].strip())
                    self.PcdValueDict[p[0].strip()] = p[2].strip()
                    self.Logger.debug("Found a Pcd in a Module Override section: %s" % p[0].strip())

            else:
                if (".inf" in line_resolved.lower()):
                    p = self.ParseInfPathMod(line_resolved)
                    self.OtherMods.append(p)
                    self.Logger.debug("Found Module: %s" % p)

            self.ParsingInBuildOption = self.ParsingInBuildOption + line_resolved.count("{")
            self.ParsingInBuildOption = self.ParsingInBuildOption - line_resolved.count("}")
            return (line_resolved, [], None)

        # process line in library class section (don't use full name)
        elif (self.CurrentSection.upper() == "LIBRARYCLASSES"):
            if (".inf" in line_resolved.lower()):
                p = self.ParseInfPathLib(line_resolved)
                self.Libs.append(p)
                self.Logger.debug("Found Library in Library Class Section: %s" % p)
            return (line_resolved, [], None)
        # process line in PCD section
        elif (self.CurrentSection.upper().startswith("PCDS")):
            if "tokenspaceguid" in line_resolved.lower() and \
                    line_resolved.count('|') > 0 and line_resolved.count('.') > 0:
                # should be a pcd statement
                p = line_resolved.partition('|')
                self.Pcds.append(p[0].strip())
                self.PcdValueDict[p[0].strip()] = p[2].strip()
                self.Logger.debug("Found a Pcd in a PCD section: %s" % p[0].strip())
            return (line_resolved, [], None)
        else:
            return (line_resolved, [], None)

    def __ParseDefineLine(self, Line):
        line_stripped = self.StripComment(Line).strip()
        if (len(line_stripped) < 1):
            return ("", [])

        # this line needs to be here to resolve any symbols inside the !include lines, if any
        line_resolved = self.ReplaceVariables(line_stripped)
        if (self.ProcessConditional(line_resolved)):
            # was a conditional
            # Other parser returns line_resolved, [].  Need to figure out which is right
            return ("", [])

        # not conditional keep processing

        # check if conditional is active
        if (not self.InActiveCode()):
            return ("", [])

        # check for include file and import lines from file
        if (line_resolved.strip().lower().startswith("!include")):
            # include line.
            tokens = line_resolved.split()
            include_file = tokens[1]
            self.Logger.debug("Opening Include File %s" % include_file)
            sp = self.FindPath(include_file)
            if sp is None:
                raise FileNotFoundError(include_file)
            self._PushTargetFile(sp)
            lf = open(sp, "r")
            loc = lf.readlines()
            lf.close()
            return ("", loc)

        # check for new section
        (IsNew, Section) = self.ParseNewSection(line_resolved)
        if (IsNew):
            self.CurrentSection = Section.upper()
            self.Logger.debug("New Section: %s" % self.CurrentSection)
            self.Logger.debug("FullSection: %s" % self.CurrentFullSection)
            return (line_resolved, [])

        # process line based on section we are in
        if (self.CurrentSection == "DEFINES") or (self.CurrentSection == "BUILDOPTIONS"):
            if line_resolved.count("=") >= 1:
                tokens = line_resolved.split("=", 1)
                leftside = tokens[0].split()
                if (len(leftside) == 2):
                    left = leftside[1]
                else:
                    left = leftside[0]
                right = tokens[1].strip()

                self.LocalVars[left] = right
                self.Logger.debug("Key,values found:  %s = %s" % (left, right))

                # iterate through the existed LocalVars and try to resolve the symbols
                for var in self.LocalVars:
                    self.LocalVars[var] = self.ReplaceVariables(self.LocalVars[var])
                return (line_resolved, [])
        else:
            return (line_resolved, [])

    def ParseInfPathLib(self, line):
        """Parses a line with an INF path Lib."""
        if (line.count("|") > 0):
            line_parts = []
            c = line.split("|")[0].strip()
            i = line.split("|")[1].strip()
            if (c in self.LibraryClassToInstanceDict):
                line_parts = self.LibraryClassToInstanceDict.get(c)
            sp = self.FindPath(i)
            line_parts.append(sp)
            self.LibraryClassToInstanceDict[c] = line_parts
            return line.split("|")[1].strip()
        else:
            return line.strip().split()[0]

    def ParseInfPathMod(self, line):
        """Parses a line with an INF path."""
        return line.strip().split()[0].rstrip("{")

    def __ProcessMore(self, lines, file_name=None):
        """Runs after ProcessDefines and does a full parsing of the DSC.

        Everything is resolved to a final state
        """
        if (len(lines) == 0):
            return
        for index in range(0, len(lines)):
            # we try here so that we can catch exceptions from individual lines
            try:
                raw_line = lines[index]
                (line, add, new_file) = self.__ParseLine(raw_line, file_name=file_name, lineno=index + 1)
                if (len(line) > 0):
                    self.Lines.append(line)
                self.__ProcessMore(add, file_name=new_file)
            except Exception as e:
                # check if we're in no fail mode or not
                if not self._no_fail_mode:  # if we are, fail
                    raise
                else:
                    # otherwise, let the user know that we failed in the DSC
                    self.Logger.warning(f"DSC Parser (No-Fail Mode): {raw_line}")
                    self.Logger.warning(e)

    def __ProcessDefines(self, lines):
        """Goes through a file once to look for [Define] sections.

        Only Sections, DEFINE, X = Y, and !includes are resolved
        This resolves all the defines since they can be anywhere in a file.
        Ideally this should be run until we reach stable state but this parser is not
        accurate and is more of an approximation of what the real parser does.
        """
        if (len(lines) == 0):
            return
        for raw_line in lines:
            # we want to catch exceptions here since we are doing includes as we potentially might blow up
            # we want to catch on a line by line basis
            try:
                (line, add) = self.__ParseDefineLine(raw_line)
                self.__ProcessDefines(add)
            except Exception:
                # Since we're going to do this in ProcessMore, don't warn people if there's an exception
                # otherwise, raise the exception and act normally
                if not self._no_fail_mode:
                    raise

    def _parse_libraries(self):
        """Builds a lookup table of all possible library instances depending on scope.

        The following is the key/value pair:
        key: The library class name with the scope appended. Examples below:
            $(LIB_NAME).$(ARCH).$(MODULE_TYPE)
            $(LIB_NAME).common.$(MODULE_TYPE)
            $(LIB_NAME).$(ARCH)
            $(LIB_NAME).common
        """
        current_scope = []
        for line in self.Lines:
            current_scope = self._get_current_scope(current_scope, line.lower(), self.SECTION_LIBRARY.lower())

            # The current section is not SECTION_LIBRARY, so we have no valid scopes. continue to next line.
            if not current_scope:
                continue

            # This line is starting a new section with a new scope. Start reading the new line
            if self.SECTION_REGEX.match(line):
                continue

            if len(line.split("|")) != 2:
                logging.debug("Unexpected Line in Library Section:")
                logging.debug(f"  {line}")
                continue

            # We are in a valid section, so lets parse the line and add it to our dictionary.
            lib, instance = tuple(line.split("|"))
            for scope in current_scope:
                key = f"{scope.strip()}.{lib.strip()}".lower()
                value = instance.strip()
                self.ScopedLibraryDict[key] = value

        return

    def _parse_components(self):
        current_scope = []
        lines = iter(self.Lines)

        try:
            while True:
                line = next(lines)

                current_scope = self._get_current_scope(current_scope, line.lower(), self.SECTION_COMPONENT)
                library_override_dict = {"NULL": []}

                # The current section is not SECTION_COMPONENT, so we have no valid scopes. continue to next line.
                if not current_scope:
                    continue

                # This line is starting a new section with a new scope. Start reading the new line
                if self.SECTION_REGEX.match(line.lower()):
                    continue

                # This component has overrides we need to handle
                if line.strip().endswith("{"):
                    line = str(line)
                    logging.debug(f"Building Library Override Dictionary for Component: {line.strip(' {')}")
                    library_override_dict = self._build_library_override_dictionary(lines)

                for scope in current_scope:
                    # Components without a specific scope (common or empty) are added to all current scopes
                    if "common" in current_scope[0]:
                        for arch in self.InputVars.get("TARGET_ARCH", "").split(" "):
                            scope = current_scope[0].replace("common", arch).lower()
                            self.Components.append((line.strip(" {"), scope, library_override_dict))
                    else:
                        self.Components.append((line.strip(" {"), current_scope[0].lower(), library_override_dict))

        except StopIteration:
            return

    def _get_current_scope(self, scope_list: list[str], line, section_type: str) -> list[str]:
        """Returns the list of scopes that this line is in, as long as the section_type is correct.

        Scopes can be different depending on the section type. Component sections can only
        contain a single scope, but library sections can contain multiple scopes.

        !!! warning
            The returned list of scopes does not include the section type.
        """
        match = self.SECTION_REGEX.match(line)

        # If the line is not a section header, return the old section
        if not match:
            return scope_list

        # If the line is a section header, but not the correct section type, return []
        elif not match.group().startswith(f"[{section_type}"):
            return []

        # The line must be a section header and of the correct section type. Return it
        current_section = []
        section_list = match.group().strip("[]").split(",")

        for section in section_list:
            # Remove the section type and strip the leftover '.'. If it's empty after that, then it is actually "common"
            section = section.replace(section_type, "").replace("Common", "common").strip().lstrip(".")
            current_section.append(section or "common")
        return current_section

    def _build_library_override_dictionary(self, lines):
        library_override_dictionary = {"NULL": []}
        section = ""

        for line in lines:
            l_line = line.lower().strip()

            if l_line == "}":
                break

            if self.OVERRIDE_REGEX.match(l_line):
                if l_line == f"<{self.SECTION_LIBRARY}>":
                    section = self.SECTION_LIBRARY
                else: # Add more sections here if needed
                    section = ""
                continue

            if section == self.SECTION_LIBRARY:
                logging.debug(f"  Library Section Override: {line}")
                lib, instance = map(str.strip, line.split("|"))
                lib = lib.lower()

                if lib == "null":
                    library_override_dictionary["NULL"].append(instance)
                else:
                    library_override_dictionary[lib] = instance
        return library_override_dictionary

    def SetNoFailMode(self, enabled=True):
        """The parser won't throw exceptions when this is turned on.

        WARNING: This can result in some weird behavior
        """
        self._no_fail_mode = enabled

    def ResetParserState(self):
        """Resets the parser."""
        #
        # add more DSC parser based state reset here, if necessary
        #
        super(DscParser, self).ResetParserState()

    def ParseFile(self, filepath):
        """Parses the DSC file at the provided path."""
        self.Logger.debug("Parsing file: %s" % filepath)
        sp = self.FindPath(filepath)
        if sp is None:
            raise FileNotFoundError(filepath)
        self._PushTargetFile(sp)
        f = open(sp, "r")
        # expand all the lines and include other files
        file_lines = f.readlines()
        self.__ProcessDefines(file_lines)
        # reset the parser state before processing more
        self.ResetParserState()
        self._PushTargetFile(sp)
        self.__ProcessMore(file_lines, file_name=sp)
        f.close()

        self._parse_libraries()
        self._parse_components()
        self.Parsed = True

    def _PushTargetFile(self, targetFile):
        self.TargetFilePath = os.path.abspath(targetFile)
        self._dsc_file_paths.add(self.TargetFilePath)

    def GetMods(self):
        """Returns a list with all Mods."""
        return self.ThreeMods + self.SixMods

    def GetModsEnhanced(self):
        """Returns a list with all ModsEnhanced."""
        return self.ThreeModsEnhanced + self.SixModsEnhanced

    def GetLibs(self):
        """Returns a list with all Libs."""
        return self.Libs

    def GetLibsEnhanced(self):
        """Returns a list with all LibsEnhanced."""
        return self.LibsEnhanced

    def GetAllDscPaths(self):
        """Returns a list with all the paths that this DSC uses (the base file and any includes).

        They are not all guaranteed to be DSC files
        """
        return self._dsc_file_paths
