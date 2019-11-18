# @file BaseParser.py
# Code to support parsing EDK2 files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import os
import logging


class BaseParser(object):
    """ """

    def __init__(self, log):
        self.Logger = logging.getLogger(log)
        self.Lines = []
        self.LocalVars = {}
        self.InputVars = {}
        self.CurrentSection = ""
        self.CurrentFullSection = ""
        self.Parsed = False
        self.ConditionalStack = []
        self.RootPath = ""
        self.PPs = []
        self.TargetFile = None
        self.TargetFilePath = None
        self._MacroNotDefinedValue = "0"  # value to used for undefined macro

    #
    # For include files set the base root path
    #

    def SetBaseAbsPath(self, path):
        """

        Args:
          path:

        Returns:

        """
        self.RootPath = path
        return self

    def SetPackagePaths(self, pps=[]):
        """

        Args:
          pps:  (Default value = [])

        Returns:

        """
        self.PPs = pps
        return self

    def SetInputVars(self, inputdict):
        """

        Args:
          inputdict:

        Returns:

        """
        self.InputVars = inputdict
        return self

    def FindPath(self, *p):
        """

        Args:
          *p:

        Returns:

        """
        # NOTE: Some of this logic should be replaced
        #       with the path resolution from Edk2Module code.

        # If the absolute path exists, return it.
        Path = os.path.join(self.RootPath, *p)
        if os.path.exists(Path):
            return Path

        # If that fails, check a path relative to the target file.
        if self.TargetFilePath is not None:
            Path = os.path.join(self.TargetFilePath, *p)
            if os.path.exists(Path):
                return Path

        # If that fails, check in every possible Pkg path.
        for Pkg in self.PPs:
            Path = os.path.join(self.RootPath, Pkg, *p)
            if os.path.exists(Path):
                return Path

        # log invalid file path
        Path = os.path.join(self.RootPath, *p)
        self.Logger.error("Invalid file path %s" % Path)
        return Path

    def WriteLinesToFile(self, filepath):
        """

        Args:
          filepath:

        Returns:

        """
        self.Logger.debug("Writing all lines to file: %s" % filepath)
        f = open(filepath, "w")
        for l in self.Lines:
            f.write(l + "\n")
        f.close()
    #
    # do logical comparisons
    #

    def ComputeResult(self, value, cond, value2):
        """

        Args:
          value:
          cond:
          value2:

        Returns:

        """
        if(cond == "=="):
            # equal
            return (value.upper() == value2.upper())

        elif (cond == "!="):
            # not equal
            return (value.upper() != value2.upper())

        elif (cond == "<"):
            return (self.ConvertToInt(value) < (self.ConvertToInt(value2)))

        elif (cond == "<="):
            return (self.ConvertToInt(value) <= (self.ConvertToInt(value2)))

        elif (cond == ">"):
            return (self.ConvertToInt(value) > (self.ConvertToInt(value2)))

        elif (cond == ">="):
            return (self.ConvertToInt(value) >= (self.ConvertToInt(value2)))

    #
    # convert to int based on prefix
    #

    def ConvertToInt(self, value):
        """

        Args:
          value:

        Returns:

        """
        if(value.upper().startswith("0X")):
            return int(value, 16)
        else:
            return int(value, 10)

    #
    # Push new value on stack
    #
    def PushConditional(self, v):
        """

        Args:
          v:

        Returns:

        """
        self.ConditionalStack.append(v)

    #
    # Pop conditional and return the value
    #

    def PopConditional(self):
        """ """
        if(len(self.ConditionalStack) > 0):
            return self.ConditionalStack.pop()
        else:
            self.Logger.critical("Tried to pop an empty conditional stack.  Line Number %d" % self.CurrentLine)
            return self.ConditionalStack.pop()  # this should cause a crash but will give trace.

    def _FindReplacementForToken(self, token):

        v = self.LocalVars.get(token)

        if(v is None):
            v = self.InputVars.get(token)

        if(v is None):
            v = self._MacroNotDefinedValue

        if (type(v) is bool):
            v = "true" if v else "false"

        if(type(v) is str and (v.upper() == "TRUE" or v.upper() == "FALSE")):
            v = v.upper()

        return v

    #
    # Method to replace variables
    # in a line with their value from input dict or local dict
    #
    def ReplaceVariables(self, line):
        """

        Args:
          line:

        Returns:

        """
        # first tokenize and look for tokens require special macro
        # handling without $.  This must be done first otherwise
        # both syntax options can not be supported.
        result = line
        tokens = result.split()
        if tokens[0].lower() in ["!ifdef", "!ifndef"]:
            if len(tokens) > 1 and not tokens[1].startswith("$("):
                v = self._FindReplacementForToken(tokens[1])
                result = result.replace(tokens[1], v, 1)

        # use line to avoid change by handling above
        rep = line.count("$")
        index = 0
        while(rep > 0):
            start = line.find("$(", index)
            end = line.find(")", start)

            token = line[start + 2:end]
            replacement_token = line[start:end + 1]
            self.Logger.debug("Token is %s" % token)
            v = self._FindReplacementForToken(token)
            result = result.replace(replacement_token, v, 1)

            index = end + 1
            rep = rep - 1

        return result

    #
    # Process Conditional
    # return true if line is a conditional otherwise false
    #

    def ProcessConditional(self, text):
        """

        Args:
          text:

        Returns:

        """
        tokens = text.split()
        if(tokens[0].lower() == "!if"):
            # need to add support for OR/AND
            if(len(tokens) < 4):
                self.Logger.error("!if conditionals need to be formatted correctly (spaces between each token)")
                raise Exception("Invalid conditional", text)
            con = self.ComputeResult(tokens[1].strip(), tokens[2].strip(), tokens[3].strip())
            self.PushConditional(con)
            return True

        elif(tokens[0].lower() == "!ifdef"):
            self.PushConditional((tokens[1] != self._MacroNotDefinedValue))
            return True

        elif(tokens[0].lower() == "!ifndef"):
            self.PushConditional((tokens[1] == self._MacroNotDefinedValue))
            return True

        elif(tokens[0].lower() == "!else"):
            v = self.PopConditional()
            self.PushConditional(not v)
            return True

        elif(tokens[0].lower() == "!endif"):
            self.PopConditional()
            return True

        return False

    #
    # returns true or false depending on what state of conditional you are currently in
    #
    def InActiveCode(self):
        """ """
        ret = True
        for a in self.ConditionalStack:
            if not a:
                ret = False
                break

        return ret

    #
    # will return true if the the line has
    # { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}
    #

    def IsGuidString(self, l):
        """

        Args:
          l:

        Returns:

        """
        if(l.count("{") == 2 and l.count("}") == 2 and l.count(",") == 10 and l.count("=") == 1):
            return True
        return False

    def ParseGuid(self, l):
        """

        Args:
          l:

        Returns:

        """
        # parse a guid in format
        # { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}
        # into F7FDE4A6-294C-493c-B50F-9734553BB757  (NOTE these are not same guid this is just example of format)
        entries = l.lstrip(' {').rstrip(' }').split(',')
        gu = entries[0].lstrip(' 0').lstrip('x').strip()
        # pad front until 8 chars
        while(len(gu) < 8):
            gu = "0" + gu

        gut = entries[1].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 4):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[2].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 4):
            gut = "0" + gut
        gu = gu + "-" + gut

        # strip off extra {
        gut = entries[3].lstrip(' { 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[4].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[5].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[6].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[7].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[8].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[9].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[10].split()[0].lstrip(' 0').lstrip('x').rstrip(' } ').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        return gu.upper()

    def ResetParserState(self):
        """ """
        self.ConditionalStack = []
        self.CurrentSection = ''
        self.CurrentFullSection = ''
        self.Parsed = False

#
# Base Class for Edk2 build files that use # for comments
#


class HashFileParser(BaseParser):
    """ """

    def __init__(self, log):
        BaseParser.__init__(self, log)

    def StripComment(self, l):
        """

        Args:
          l:

        Returns:

        """
        return l.split('#')[0].strip()

    def ParseNewSection(self, l):
        """

        Args:
          l:

        Returns:

        """
        if(l.count("[") == 1 and l.count("]") == 1):  # new section
            section = l.strip().lstrip("[").split(".")[0].split(",")[0].rstrip("]").strip()
            self.CurrentFullSection = l.strip().lstrip("[").split(",")[0].rstrip("]").strip()
            return (True, section)
        return (False, "")
