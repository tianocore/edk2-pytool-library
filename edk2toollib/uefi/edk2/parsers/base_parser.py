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

    def __init__(self, log=""):
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
        self.CurrentLine = -1

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
        ivalue = value
        ivalue2 = value2
        # convert it to interpretted value

        try:
            ivalue = self.ConvertToInt(ivalue)
        except ValueError:
            self.Logger.warning(f"{self.__class__}: Cannot convert value to an int: {ivalue}")
        try:
            ivalue2 = self.ConvertToInt(ivalue2)
        except ValueError:
            self.Logger.warning(f"{self.__class__}: Cannot convert value to an int: {ivalue2}")


        # check our truthyness
        if(cond == "=="):
            # equal
            return (ivalue == ivalue2) or (value == value2)

        elif (cond == "!="):
            # not equal
            return (ivalue != ivalue2) or (value != value2)

        # check to make sure we only have digits from here on out
        if not str.isdigit(value):
            self.Logger.error(f"{self.__class__}: Unknown value: {value} {ivalue.__class__}")
            self.Logger.debug(f"{self.__class__}: Conditional: {value} {cond}{value2}")
            raise ValueError("Unknown value")

        if not str.isdigit(value2):
            self.Logger.error(f"{self.__class__}: Unknown value: {value2} {ivalue2}")
            self.Logger.debug(f"{self.__class__}: Conditional: {value} {cond} {value2}")
            raise ValueError("Unknown value")

        if (cond == "<"):
            return (ivalue < ivalue2)

        elif (cond == "<="):
            return (ivalue <= ivalue2)

        elif (cond == ">"):
            return (ivalue > ivalue2)

        elif (cond == ">="):
            return (ivalue >= ivalue2)

        else:
            self.Logger.error(f"{self.__class__}: Unknown conditional: {cond}")
            raise RuntimeError("Unknown conditional")

    #
    # convert to int based on prefix
    #

    def ConvertToInt(self, value):
        """

        Args:
          value: must be str or int

        Returns:

        """
        if isinstance(value, str) and value.upper() == "TRUE":
            return 1
        elif isinstance(value, str) and value.upper() == "FALSE":
            return 0
        elif isinstance(value, str) and value.upper().startswith("0X"):
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
        rep = line.count("$")
        result = line
        index = 0
        while(rep > 0):
            start = line.find("$(", index)
            end = line.find(")", start)

            token = line[start + 2:end]
            retoken = line[start:end + 1]
            self.Logger.debug("Token is %s" % token)
            v = self.LocalVars.get(token)
            self.Logger.debug("Trying to replace %s" % retoken)
            if(v is not None):
                v = str(v)
                #
                # fixme: This should just be a workaround!!!!!
                #
                if (v.upper() == "TRUE" or v.upper() == "FALSE"):
                    v = v.upper()
                self.Logger.debug("with %s  [From Local Vars]" % v)
                result = result.replace(retoken, v, 1)
            else:
                # use the passed in Env
                v = self.InputVars.get(token)

                if(v is None):
                    self.Logger.error("Unknown variable %s in  %s" % (token, line))
                    # raise RuntimeError("Invalid Variable Replacement", token)
                    # just skip it because we need to support ifdef
                else:
                    v = str(v)
                    # found in the Env
                    #
                    # fixme: This should just be a workaround!!!!!
                    #
                    if (v.upper() == "TRUE" or v.upper() == "FALSE"):
                        v = v.upper()
                    self.Logger.debug("with %s [From Input Vars]" % v)
                    result = result.replace(retoken, v, 1)

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
            if (len(tokens) == 2):
                value = self.ConvertToInt(tokens[1].strip())
                self.PushConditional(value == 1)  # if the value is true
            # we can have tokens in 4, 8, 12 etc
            elif len(tokens) >= 4 and len(tokens) % 4 == 0:
                con = self.ComputeResult(tokens[1].strip(), tokens[2].strip(), tokens[3].strip())
                self.PushConditional(con)
            else:
                self.Logger.error("!if conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            return True

        elif(tokens[0].lower() == "!ifdef"):
            if len(tokens) != 2:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            self.PushConditional((tokens[1].count("$") == 0))
            return True

        elif(tokens[0].lower() == "!ifndef"):
            if len(tokens) != 2:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            self.PushConditional((tokens[1].count("$") > 0))
            return True

        elif(tokens[0].lower() == "!else"):
            if len(tokens) != 1:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
            v = self.PopConditional()
            # TODO make sure we can't do multiple else statements
            self.PushConditional(not v)
            return True

        elif(tokens[0].lower() == "!endif"):
            if len(tokens) != 1:
                self.Logger.error("!ifdef conditionals need to be formatted correctly (spaces between each token)")
                raise RuntimeError("Invalid conditional", text)
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

    def IsGuidString(self, l):
        """
        will return true if the the line has
        = { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}
        Args:
          l:

        Returns:

        """
        if(l.count("{") == 2 and l.count("}") == 2 and l.count(",") == 10 and l.count("=") == 1):
            return True
        return False

    def ParseGuid(self, l):
        """
        parse a guid into a different format
        Will throw exception if missing any of the 11 parts of isn't long enough
        Args:
          l: the guid to parse ex: { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}

        Returns: a string of the guid. ex: D3B36F2C-D551-11D4-9A46-0090273FC14D

        """
        entries = l.lstrip(' {').rstrip(' }').split(',')
        if len(entries) != 11:
            raise RuntimeError(f"Invalid GUID found {l}. We are missing some parts since we only found: {len(entries)}")
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

        proper_guid_length = 36
        if len(gu) > proper_guid_length:
            raise RuntimeError(f"The guid we parsed was too long: {gu}")
        if len(gu) < proper_guid_length:
            raise RuntimeError(f"The guid we parsed was too short: {gu}")

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
