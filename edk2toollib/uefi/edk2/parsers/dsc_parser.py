# @file dsc_parser.py
# Code to help parse DSC files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser
import os


class DscParser(HashFileParser):

    def __init__(self):
        super(DscParser, self).__init__('DscParser')
        self.SixMods = []
        self.SixModsEnhanced = []
        self.ThreeMods = []
        self.ThreeModsEnhanced = []
        self.OtherMods = []
        self.Libs = []
        self.LibsEnhanced = []
        self.ParsingInBuildOption = 0
        self.LibraryClassToInstanceDict = {}
        self.Pcds = []
        self._no_fail_mode = False
        self._dsc_file_paths = set()  # This includes the full paths for every DSC that makes up the file

    def __ParseLine(self, Line, file_name=None, lineno=None):
        line_stripped = self.StripComment(Line).strip()
        if(len(line_stripped) < 1):
            return ("", [], None)

        line_resolved = self.ReplaceVariables(line_stripped)
        if(self.ProcessConditional(line_resolved)):
            # was a conditional
            # Other parser returns line_resolved, [].  Need to figure out which is right
            return ("", [], None)

        # not conditional keep procesing

        # check if conditional is active
        if(not self.InActiveCode()):
            return ("", [], None)

        # check for include file and import lines from file
        if(line_resolved.strip().lower().startswith("!include")):
            # include line.
            tokens = line_resolved.split()
            self.Logger.debug("Opening Include File %s" % os.path.join(self.RootPath, tokens[1]))
            sp = self.FindPath(tokens[1])
            self._dsc_file_paths.add(sp)
            lf = open(sp, "r")
            loc = lf.readlines()
            lf.close()
            return ("", loc, sp)

        # check for new section
        (IsNew, Section) = self.ParseNewSection(line_resolved)
        if(IsNew):
            self.CurrentSection = Section.upper()
            self.Logger.debug("New Section: %s" % self.CurrentSection)
            self.Logger.debug("FullSection: %s" % self.CurrentFullSection)
            return (line_resolved, [], None)

        # process line in x64 components
        if(self.CurrentFullSection.upper() == "COMPONENTS.X64"):
            if(self.ParsingInBuildOption > 0):
                if(".inf" in line_resolved.lower()):
                    p = self.ParseInfPathLib(line_resolved)
                    self.Libs.append(p)
                    self.Logger.debug("Found Library in a 64bit BuildOptions Section: %s" % p)
                elif "tokenspaceguid" in line_resolved.lower() and \
                        line_resolved.count('|') > 0 and line_resolved.count('.') > 0:
                    # should be a pcd statement
                    p = line_resolved.partition('|')
                    self.Pcds.append(p[0].strip())
                    self.Logger.debug("Found a Pcd in a 64bit Module Override section: %s" % p[0].strip())
            else:
                if(".inf" in line_resolved.lower()):
                    p = self.ParseInfPathMod(line_resolved)
                    self.SixMods.append(p)
                    if file_name is not None and lineno is not None:
                        self.SixModsEnhanced.append({'file': os.path.normpath(file_name), 'lineno': lineno, 'data': p})
                    self.Logger.debug("Found 64bit Module: %s" % p)

            self.ParsingInBuildOption = self.ParsingInBuildOption + line_resolved.count("{")
            self.ParsingInBuildOption = self.ParsingInBuildOption - line_resolved.count("}")
            return (line_resolved, [], None)

        # process line in ia32 components
        elif(self.CurrentFullSection.upper() == "COMPONENTS.IA32"):
            if(self.ParsingInBuildOption > 0):
                if(".inf" in line_resolved.lower()):
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
                    self.Logger.debug("Found a Pcd in a 32bit Module Override section: %s" % p[0].strip())

            else:
                if(".inf" in line_resolved.lower()):
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
        elif("COMPONENTS" in self.CurrentFullSection.upper()):
            if(self.ParsingInBuildOption > 0):
                if(".inf" in line_resolved.lower()):
                    p = self.ParseInfPathLib(line_resolved)
                    self.Libs.append(p)
                    self.Logger.debug("Found Library in a BuildOptions Section: %s" % p)
                elif "tokenspaceguid" in line_resolved.lower() and \
                        line_resolved.count('|') > 0 and line_resolved.count('.') > 0:
                    # should be a pcd statement
                    p = line_resolved.partition('|')
                    self.Pcds.append(p[0].strip())
                    self.Logger.debug("Found a Pcd in a Module Override section: %s" % p[0].strip())

            else:
                if(".inf" in line_resolved.lower()):
                    p = self.ParseInfPathMod(line_resolved)
                    self.OtherMods.append(p)
                    self.Logger.debug("Found Module: %s" % p)

            self.ParsingInBuildOption = self.ParsingInBuildOption + line_resolved.count("{")
            self.ParsingInBuildOption = self.ParsingInBuildOption - line_resolved.count("}")
            return (line_resolved, [], None)

        # process line in library class section (don't use full name)
        elif(self.CurrentSection.upper() == "LIBRARYCLASSES"):
            if(".inf" in line_resolved.lower()):
                p = self.ParseInfPathLib(line_resolved)
                self.Libs.append(p)
                self.Logger.debug("Found Library in Library Class Section: %s" % p)
            return (line_resolved, [], None)
        # process line in PCD section
        elif(self.CurrentSection.upper().startswith("PCDS")):
            if "tokenspaceguid" in line_resolved.lower() and \
                    line_resolved.count('|') > 0 and line_resolved.count('.') > 0:
                # should be a pcd statement
                p = line_resolved.partition('|')
                self.Pcds.append(p[0].strip())
                self.Logger.debug("Found a Pcd in a PCD section: %s" % p[0].strip())
            return (line_resolved, [], None)
        else:
            return (line_resolved, [], None)

    def __ParseDefineLine(self, Line):
        line_stripped = self.StripComment(Line).strip()
        if(len(line_stripped) < 1):
            return ("", [])

        # this line needs to be here to resolve any symbols inside the !include lines, if any
        line_resolved = self.ReplaceVariables(line_stripped)
        if(self.ProcessConditional(line_resolved)):
            # was a conditional
            # Other parser returns line_resolved, [].  Need to figure out which is right
            return ("", [])

        # not conditional keep procesing

        # check if conditional is active
        if(not self.InActiveCode()):
            return ("", [])

        # check for include file and import lines from file
        if(line_resolved.strip().lower().startswith("!include")):
            # include line.
            tokens = line_resolved.split()
            self.Logger.debug("Opening Include File %s" % os.path.join(self.RootPath, tokens[1]))
            sp = self.FindPath(tokens[1])
            lf = open(sp, "r")
            loc = lf.readlines()
            lf.close()
            return ("", loc)

        # check for new section
        (IsNew, Section) = self.ParseNewSection(line_resolved)
        if(IsNew):
            self.CurrentSection = Section.upper()
            self.Logger.debug("New Section: %s" % self.CurrentSection)
            self.Logger.debug("FullSection: %s" % self.CurrentFullSection)
            return (line_resolved, [])

        # process line based on section we are in
        if(self.CurrentSection == "DEFINES") or (self.CurrentSection == "BUILDOPTIONS"):
            if line_resolved.count("=") >= 1:
                tokens = line_resolved.split("=", 1)
                leftside = tokens[0].split()
                if(len(leftside) == 2):
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
        if(line.count("|") > 0):
            line_parts = []
            c = line.split("|")[0].strip()
            i = line.split("|")[1].strip()
            if(c in self.LibraryClassToInstanceDict):
                line_parts = self.LibraryClassToInstanceDict.get(c)
            sp = self.FindPath(i)
            line_parts.append(sp)
            self.LibraryClassToInstanceDict[c] = line_parts
            return line.split("|")[1].strip()
        else:
            return line.strip().split()[0]

    def ParseInfPathMod(self, line):
        return line.strip().split()[0].rstrip("{")

    def __ProcessMore(self, lines, file_name=None):
        '''
        ProcessMore runs after ProcessDefines and does a full parsing of the DSC
        Everything is resolved to a final state
        '''
        if(len(lines) == 0):
            return
        for index in range(0, len(lines)):
            # we try here so that we can catch exceptions from individual lines
            try:
                (line, add, new_file) = self.__ParseLine(lines[index], file_name=file_name, lineno=index + 1)
                if(len(line) > 0):
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
        '''
        ProcessDefines goes through a file once to look for [Define] sections.
        Only Sections, DEFINE, X = Y, and !includes are resolved
        This resolves all the defines since they can be anywhere in a file.
        Ideally this should be run until we reach stable state but this parser is not
        accurate and is more of an approximation of what the real parser does.
        '''

        if(len(lines) == 0):
            return
        for raw_line in lines:
            # we want to catch exceptions here since we are doing includes as we potentially might blow up
            # we want to catch on a line by line basis
            try:
                (line, add) = self.__ParseDefineLine(raw_line)
                self.__ProcessDefines(add)
            except Exception as e:
                # Since we're going to do this in ProcessMore, don't warn people if there's an exception
                # otherwise, raise the exception and act normally
                if not self._no_fail_mode:
                    raise

    def SetNoFailMode(self, enabled=True):
        '''
        The parser won't throw exceptions when this is turned on
        This can result in some weird behavior
        '''
        self._no_fail_mode = enabled

    def ResetParserState(self):
        #
        # add more DSC parser based state reset here, if necessary
        #
        super(DscParser, self).ResetParserState()

    def ParseFile(self, filepath):
        self.Logger.debug("Parsing file: %s" % filepath)
        self.TargetFile = os.path.abspath(filepath)
        self.TargetFilePath = os.path.dirname(self.TargetFile)
        sp = os.path.join(filepath)
        self._dsc_file_paths.add(sp)
        f = open(sp, "r")
        # expand all the lines and include other files
        file_lines = f.readlines()
        self.__ProcessDefines(file_lines)
        # reset the parser state before processing more
        self.ResetParserState()
        self.__ProcessMore(file_lines, file_name=sp)
        f.close()
        self.Parsed = True

    def GetMods(self):
        return self.ThreeMods + self.SixMods

    def GetModsEnhanced(self):
        return self.ThreeModsEnhanced + self.SixModsEnhanced

    def GetLibs(self):
        return self.Libs

    def GetLibsEnhanced(self):
        return self.LibsEnhanced

    def GetAllDscPaths(self):
        ''' returns an iterable with all the paths that this DSC uses (the base file and any includes).
            They are not all guaranteed to be DSC files '''
        return self._dsc_file_paths
